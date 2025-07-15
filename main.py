import os
from Parser import CSharpFile
from helper import create_globals, globals

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    cs_file = os.path.join(current_dir, "to_parse.cs")

    # with open(cs_file, "r") as file:
    #     to_parse = file.read()

    to_parse = """
public sealed class Admin_Share_Recipients : APITest
{
    private string Endpoint = $"gl-share/api/Admin/share";

    private string EndpointWithShareLink(string shareLink) => $"{Endpoint}/{shareLink}/recipients";

    private string anothervar = $"{EndpointWithShareLink("somelink/ink")}";
}
"""

#     [Test]
#     [Data.SetUp(Tokens.TokenAdminAPI, Tokens.TokenBasicUserAPI, Shares.KkomradeNoMessage)]
#     [Recycle(Recycled.TokenAdminAPI)]
#     [Swagger(Path = Paths.None, Operation = OperationType.Post, ResponseCode = 200)]
#     public void POST_AdminShareRecipients_AddRecipient_200_141306()
#     {
#         var token = Get<Token>(Tokens.TokenAdminAPI);
#         var shareGroup = Get<ShareGroup>(Shares.KkomradeNoMessage);
#         Models.User toAdd = Get<Models.User>(Users.BasicTierUser);
#         Recipient recipient = (Recipient)toAdd with
#         {
#             UserWhoAddedRecipient = token.User.Email,

#         };
#     }
# }
# """

    globals_env = create_globals(globals)
    cs = CSharpFile(to_parse, globals=globals_env)
    for _class in cs.get_classes():
        print(f"Class: {_class.class_name}")
        print(f"Attributes: {_class.attributes}")
        print(f"Super Class: {_class.super_class_name}")
        print("Class Environment:")
        for var_name, type_obj in _class.environment.values.items():
            print(f"  {var_name}: {type_obj} (type: {type_obj.cstype})")
        print("Methods:")
        for method in _class.get_methods():
            print(f"  Method: {method.method_name}")
            print(f"    Attributes: {method.attributes}")
            print(f"    Method Environment:")
            for var_name, type_obj in method.environment.values.items():
                print(f"      {var_name}: {type_obj} (type: {type_obj.cstype})")
        print()

    