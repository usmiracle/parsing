using TransPerfect.Automation.Framework.Swagger;
using Microsoft.OpenApi.Models;
namespace Tests.API.ApprovalLinks;

[Parallelizable(ParallelScope.All)]
[ReadFrom(
    "DataProviders/{env}env.json",
    "DataProviders/{env}{browser}/users.json",
    "DataProviders/fileConfig.json",
    "DataProviders/Tokens/{env}.json"
)]

public sealed class Admin_Share_Recipients : APITest
{
    private string Endpoint => $"{GlobalLabShare}/gl-share/api/Admin/share";

    private string EndpointWithShareLink(string shareLink) => $"{Endpoint}/{shareLink}/recipients";

    [Test]
    [Data.SetUp(Tokens.TokenAdminAPI, Tokens.TokenBasicUserAPI, Shares.KkomradeNoMessage)]
    [Recycle(Recycled.TokenAdminAPI)]
    [Swagger(Path = Paths.None, Operation = OperationType.Post, ResponseCode = 200)]
    public void POST_AdminShareRecipients_AddRecipient_200_141306()
    {
        var token = Get<Token>(Tokens.TokenAdminAPI);
        var shareGroup = Get<ShareGroup>(Shares.KkomradeNoMessage);
        Models.User toAdd = Get<Models.User>(Users.BasicTierUser);
        Recipient recipient = (Recipient)toAdd with
        {
            UserWhoAddedRecipient = token.User.Email,

        };

        var shareResponseBeforeAdd = shareGroup.GetShareResponse();

        Verify(shareResponseBeforeAdd?.Recipients.Any(r => r.EmailAddress == toAdd.Email), "Share does not contain recipient").Succintly.Is(false);

        Send(
            Post<List<Recipient>>([recipient]).To(EndpointWithShareLink(shareGroup.Share.Id)) with
            { Authorization = Bearer(token.AccessToken) }
        );

        Verify(Response.StatusCode).Is(OK);
        Verify(Response.Content.As<string>(SerializationFormat.Text)).Is($"Recipients have been added to {shareGroup.Share.Id}.");

        var shareResponseAfterAdd = shareGroup.GetShareResponse();

        Verify(shareResponseAfterAdd?.Recipients.Any(r => r.EmailAddress == toAdd.Email), "Share contains added recipient").Succintly.Is(true);
    }
}
