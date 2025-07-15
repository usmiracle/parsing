using Models.Requests;
using Models.Responses;

namespace Tests.API.AdminInfo;

[NonParallelizable]
[ReadFrom(
    "DataProviders/{env}{browser}/users.json",
    "DataProviders/{env}env.json",
    "DataProviders/Tokens/{env}.json"
)]
public sealed class Admin_External_Pricing_Update : APITest
{
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/user/external/pricing";
    private static PricingFeatureModel PollForExpectedPricingType(Token token, int expectedPricingType)
    {
        using var poller =
        new Poller<PricingFeatureModel>(token.User.GetUserPermission, response => response.PricingTypeId == expectedPricingType)
        {
            Interval = TimeSpan.FromSeconds(1),
            Timeout = TimeSpan.FromSeconds(10),
        };
        return poller.Result;
    }
    private static PricingFeatureModel PollForExpectedTrialStatus(Token token, bool expectedTrialStatus)
    {
        using var poller =
        new Poller<PricingFeatureModel>(token.User.GetUserPermission, response => response.IsTrialEnabled == expectedTrialStatus)
        {
            Interval = TimeSpan.FromSeconds(1),
            Timeout = TimeSpan.FromSeconds(10),
        };
        return poller.Result;
    }

    private PricingFeatureModel PollToChangeTrialStatus(Token admin, Token client, UpdateExternalUserPricingModel request, bool expectedTrialStatus)
    {
        var giveTrial = () =>
        {
            Send(
                Post(request).To($"{GlobalLabShare}/gl-share/api/Admin/User/external/pricing" + APIVersion) with
                { Authorization = Bearer(admin.AccessToken) });
            return client.User.GetUserPermission();
        };

        using var poller =
        new Poller<PricingFeatureModel>(
            giveTrial,
            response => response.IsTrialEnabled == expectedTrialStatus)
        {
            Interval = TimeSpan.FromSeconds(2),
            Timeout = TimeSpan.FromSeconds(20),
        };
        return poller.Result;
    }

    private bool PollForResponseOK(Token admin, UpdateExternalUserPricingModel request)
    {
        var sendRequest = () =>
        {
            Send(
                Post(request).To($"{GlobalLabShare}/gl-share/api/Admin/User/external/pricing" + APIVersion) with
                { Authorization = Bearer(admin.AccessToken) });

            return Response.StatusCode == OK;
        };

        using var poller =
        new Poller<bool>(sendRequest, response => response)
        {
            Interval = TimeSpan.FromSeconds(1),
            Timeout = TimeSpan.FromSeconds(10),
        };
        return poller.Result;
    }

    private static PricingFeatureModel PollForExpectedTrialExpiration(Token token, DateTime? date)
    {
        using var poller =
        new Poller<PricingFeatureModel>(token.User.GetUserPermission, response => response.TrialExpirationDateTime.Value.Date == date)
        {
            Interval = TimeSpan.FromSeconds(1),
            Timeout = TimeSpan.FromSeconds(10),
        };
        return poller.Result;
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.AnyTierUserAPI)]
    [Recycle(Recycled.TokenAdminAPI, Recycled.AnyTierUserAPI)]
    public void POST_Admin_External_Pricing_GiveNewTrial_201_133278()
    {
        var admin = Get<Token>(Tokens.TokenAdminAPI);
        var subject = Get<Token>(Tokens.AnyTierUserAPI);
        subject.User.SetUserToken(subject);

        UpdateExternalUserPricingModel disableTrialRequest = new()
        {
            UserId = int.Parse(subject.User.Id),
            PricingTypeId = (int)PricingType.Free,
            EnableTrial = false,
        };

        Send(
            Post(disableTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        var userInfo = PollForExpectedTrialStatus(subject, false);
        Verify(userInfo?.IsTrialEnabled, "Trial disabled").Succintly.Is(false);

        var enableTrialRequest = disableTrialRequest with
        {
            PricingTypeId = (int)PricingType.Free,
            EnableTrial = true,
        };

        Send(
            Post(enableTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        Verify(Response.StatusCode).Is(Created);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is("Successfully added trial subscription for user on Subscriptions API. Status code: 201");

        userInfo = PollForExpectedTrialStatus(subject, true);
        Verify(userInfo.IsTrialEnabled, "Trial enabled");
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.AnyTierUserAPI)]
    [Recycle(Recycled.TokenAdminAPI, Recycled.AnyTierUserAPI)]
    public void POST_Admin_External_Pricing_DisableTrial_133279()
    {
        var admin = Get<Token>(Tokens.TokenAdminAPI);
        var subject = Get<Token>(Tokens.AnyTierUserAPI);
        subject.User.SetUserToken(subject);

        UpdateExternalUserPricingModel enableTrialRequest = new()
        {
            UserId = int.Parse(subject.User.Id),
            PricingTypeId = (int)PricingType.Free,
            EnableTrial = true
        };

        Send(
            Post(enableTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        var userInfo = PollForExpectedTrialStatus(subject, true);
        Verify(userInfo.IsTrialEnabled, "Trial enabled");

        var disableTrialRequest = enableTrialRequest with
        {
            EnableTrial = false,
        };

        Send(
            Post(disableTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        Verify(Response.StatusCode).Is(OK);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is("Successfully deleted trial subscription for user on Subscriptions API. Status code: 200");

        userInfo = PollForExpectedTrialStatus(subject, false);
        Verify(userInfo?.IsTrialEnabled, "Trial disabled").Succintly.Is(false);

        enableTrialRequest = enableTrialRequest with
        {
            PricingTypeId = (int)PricingType.Free,
            EnableTrial = true,
        };

        Send(
            Post(enableTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        userInfo = PollForExpectedTrialStatus(subject, true);
        Verify(userInfo.IsTrialEnabled, "Trial enabled");

        disableTrialRequest = disableTrialRequest with
        {
            PricingTypeId = (int)PricingType.Free,
            EnableTrial = false,
        };

        Send(
            Post(disableTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        Verify(Response.StatusCode).Is(OK);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is("Successfully deleted trial subscription for user on Subscriptions API. Status code: 200");

        userInfo = PollForExpectedTrialStatus(subject, false);
        Verify(userInfo?.IsTrialEnabled, "Trial disabled").Succintly.Is(false);
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.TokenInternalUser2API)]
    [Recycle(Recycled.TokenAdminAPI, Recycled.TokenInternalUser2API)]
    public void POST_Admin_External_Pricing_InternalUser_400_133281()
    {
        var admin = Get<Token>(Tokens.TokenAdminAPI);
        var subject = Get<Token>(Tokens.TokenInternalUser2API);
        subject.User.SetUserToken(subject);
        var userResponseBefore = subject.User.GetUserPermission();

        UpdateExternalUserPricingModel request = new()
        {
            UserId = int.Parse(subject.User.Id),
            PricingTypeId = (int)PricingType.Pro
        };

        Send(
            Post(request).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        Verify(Response.StatusCode).Is(BadRequest);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is("Invalid user passed for external user pricing type updates. Only external users are supported");
        var userResponseAfter = subject.User.GetUserPermission();
        Verify(userResponseBefore, "User details are unchanged").Succintly.Is(userResponseAfter);
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.AnyTierUserAPI)]
    [Recycle(Recycled.TokenAdminAPI, Recycled.AnyTierUserAPI)]
    public void POST_Admin_External_Pricing_ChangeTrialDaysRemaining_200_133282()
    {
        var admin = Get<Token>(Tokens.TokenAdminAPI);
        var subject = Get<Token>(Tokens.AnyTierUserAPI);
        subject.User.SetUserToken(subject);

        UpdateExternalUserPricingModel enableTrialRequest = new()
        {
            UserId = int.Parse(subject.User.Id),
            PricingTypeId = (int)PricingType.Free,
            EnableTrial = true,
        };

        Send(
            Post(enableTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );
        PollForExpectedPricingType(subject, enableTrialRequest.PricingTypeId);
        var userInfo = PollForExpectedTrialStatus(subject, true);
        Verify(userInfo.PricingTypeId).Is(enableTrialRequest.PricingTypeId);
        Verify(userInfo.IsTrialEnabled, "Trial enabled");
        var days = 5;
        var shortenTrialRequest = enableTrialRequest with
        {
            TrialEndDate = DateTime.UtcNow.AddDays(days),
        };

        Send(
            Post(shortenTrialRequest).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );
        Verify(Response.StatusCode).Is(OK);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is("Successfully updated trial subscription expiration date for user on Subscriptions API. Status code: 200");

        PollForExpectedTrialStatus(subject, true);
        userInfo = PollForExpectedTrialExpiration(subject, shortenTrialRequest.TrialEndDate);

        Verify(userInfo.PricingTypeName).Is("Free");
        Verify(userInfo.PricingTypeId).Is((int)PricingType.Free);
        Verify(userInfo.IsTrialEnabled, "Trial enabled");

        var toSubtract = new TimeSpan(days, 0, 0, 0);

        if (DateTime.Now.IsDaylightSavingTime() && !userInfo.TrialExpirationDateTime.Value.ToLocalTime().IsDaylightSavingTime())
        {
            //EDT -> EST -- fall back one hour
            toSubtract = new TimeSpan(days, -1, 0, 0);
        }
        else if (!DateTime.Now.IsDaylightSavingTime() && userInfo.TrialExpirationDateTime.Value.ToLocalTime().IsDaylightSavingTime())
        {
            //EST -> EDT -- spring ahead one hour
            toSubtract = new TimeSpan(days, 1, 0, 0);
        }

        //Verify that expiration date (set 5 days from now) minus 5 days (+/- 1 hour) is equal to now, within one minute        
        Verify(userInfo.TrialExpirationDateTime.Value.ToLocalTime().Subtract(toSubtract), "Trial expiration date minus set days remaining").IsWithin(TimeSpan.FromMinutes(1));
    }

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.AnyTierUserAPI)]
    [Recycle(Recycled.TokenAdminAPI, Recycled.AnyTierUserAPI)]
    public void POST_Admin_External_Pricing_SendExistingPricingType_133284()
    {
        var admin = Get<Token>(Tokens.TokenAdminAPI);
        var subject = Get<Token>(Tokens.AnyTierUserAPI);
        subject.User.SetUserToken(subject);

        UpdateExternalUserPricingModel request = new()
        {
            UserId = int.Parse(subject.User.Id),
            PricingTypeId = (int)PricingType.Free,
        };

        Send(
            Post(request).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );
        var userInfo = PollForExpectedPricingType(subject, request.PricingTypeId);
        Verify(userInfo.PricingTypeName).Is(((PricingType)request.PricingTypeId).ToString());
        Verify(userInfo?.IsTrialEnabled).Is(false);

        //repeat request
        Send(
            Post(request).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );
        Verify(Response.StatusCode).Is(BadRequest);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Contains($"Could not add free subscription for user on Subscriptions API.");
        Verify(subject.User.GetUserPermission().PricingTypeId).Is(request.PricingTypeId);
        Verify(subject.User.GetUserPermission()?.IsTrialEnabled).Is(false);

        request = request with
        {
            EnableTrial = true,
        };

        Send(
            Post(request).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );

        Verify(Response.StatusCode).Is(Created);
        userInfo = PollForExpectedPricingType(subject, request.PricingTypeId);
        Verify(userInfo.PricingTypeName).Is(((PricingType)request.PricingTypeId).ToString());

        //repeat request
        Send(
            Post(request).To(Endpoint)
            with
            { Authorization = Bearer(admin.AccessToken) }
        );
        Verify(PollForResponseOK(admin, request));
        Verify(Response.StatusCode).Is(OK);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is("Successfully updated trial subscription expiration date for user on Subscriptions API. Status code: 200");
        Verify(subject.User.GetUserPermission().PricingTypeId).Is(request.PricingTypeId);
        Verify(subject.User.GetUserPermission()?.IsTrialEnabled).Is(request.EnableTrial);
    }
}
