from Environment import Environment, Type
import re

# from newvars.txt
globals = """
DownloadAPI=/api/Download
DownloadSignedKeyAPI=/api/Download/signed-key
RecipientsAPI=/api/Recipients
RecipientsRecentAPI=/api/Recipients/recent
RecipientsSearchEmailsAPI=/api/Recipients/search-emails
RecipientsSearchQueryAPI=/api/Recipients/search-query
ReportsAPI=/api/Reports
ShareAPI=/api/Share
ShareAPIv2=/api/v2/Shares
ShareActivityAPI=/api/ShareActivity
HealthAPI=/healthz
AuditLogAPI=/api/AuditLog
GeoLocation=/api/GeoLocation
UserPreferencesAPI=/api/User/preferences
UserPermissionAPI=/api/User/me
AdminBlackListAPI=/api/Admin/blacklist-organizations
DatabaseHealthAPI=/database
ServiceHealthAPI=/services
#
SQL=Tests.SQL.SQLContext
GlobalLabShare=https://qa-share.transperfect.com
GlobalLabShareNoHTTPS=qa-share.transperfect.com
DownloadAPI=https://qa-share.transperfect.com/gl-share/api/Download
DownloadSignedKeyAPI=https://qa-share.transperfect.com/gl-share/api/Download/signed-key
RecipientsAPI=https://qa-share.transperfect.com/gl-share/api/Recipients
RecipientsRecentAPI=https://qa-share.transperfect.com/gl-share/api/Recipients/recent
RecipientsSearchEmailsAPI=https://qa-share.transperfect.com/gl-share/api/Recipients/search-emails
RecipientsSearchQueryAPI=https://qa-share.transperfect.com/gl-share/api/Recipients/search-query
ReportsAPI=https://qa-share.transperfect.com/gl-share/api/Reports
ShareAPI=https://qa-share.transperfect.com/gl-share/api/Share
ShareAPIv2=https://qa-share.transperfect.com/gl-share/api/v2/Shares
ShareActivityAPI=https://qa-share.transperfect.com/gl-share/api/ShareActivity
HealthAPI=https://qa-share.transperfect.com/gl-share/healthz
AuditLogAPI=https://qa-share.transperfect.com/gl-share/api/AuditLog
GeoLocation=https://qa-share.transperfect.com/gl-share/api/GeoLocation
UserPreferencesAPI=https://qa-share.transperfect.com/gl-share/api/User/preferences
UserPermissionAPI=https://qa-share.transperfect.com/gl-share/api/User/me
AdminBlackListAPI=https://qa-share.transperfect.com/gl-share/api/Admin/blacklist-organizations
DatabaseHealthAPI=https://qa-share.transperfect.com/gl-share/database
ServiceHealthAPI=https://qa-share.transperfect.com/gl-share/services
APIVersion=?api-version=1
APIVersionBad=?api-version=0
CaRFSArchive=https://fs-qa.transperfect.com/Archives
ExpiredAuth=eyJhbGciOiJSUzI1NiIsImtpZCI6IkU4MTY2QjA0RDlBQTI5RTlFRURDNkU2QTk1RUNGNzgxMzMyQzcwNTAiLCJ0eXAiOiJKV1QiLCJ4NXQiOiI2QlpyQk5tcUtlbnUzRzVxbGV6M2dUTXNjRkEifQ.eyJuYmYiOjE2Mjg2MjI4NDUsImV4cCI6MTYyODYyNjQ0NSwiaXNzIjoiaHR0cHM6Ly9zc28tc3RnLnRyYW5zcGVyZmVjdC5jb20iLCJhdWQiOlsiaHR0cHM6Ly9zc28tc3RnLnRyYW5zcGVyZmVjdC5jb20vcmVzb3VyY2VzIiwiR0xTaGFyZUFwaSIsIkNhckZTQXBpIl0sImNsaWVudF9pZCI6IlhQOENlUnlOOUFHZ0c4bk5oQWVQY3o2Yjc3cEFnZGg5Iiwic3ViIjoiYmVzYXk1NzY1N0BiaW9ob3J0YS5jb20iLCJhdXRoX3RpbWUiOjE2Mjg2MjI4NDUsImlkcCI6IlRyYW5zUGVyZmVjdEF1dGgiLCJzY29wZSI6WyJvcGVuaWQiLCJwcm9maWxlIiwiZW1haWwiLCJ1c2VybmFtZSIsImRpcmVjdG9yeSIsIkdMU2hhcmVBcGkiLCJDYXJGU0FwaSJdLCJhbXIiOlsiZXh0ZXJuYWwiXX0.ABSYw2kPXw7Qk0aiecJBKKh7yfUsN9jpAqm4-GuXxECOSsHSj-XmBbJdQwWGR7ENXb5Hj2-uLYg1gmb5MsX_7MXnOFmUynkklt8JnhvSVF0xsAxM2tv-VYjeuXT_ZsbDiU69_dpf-PpzWB--Ph3DiTy0C6HGCMeDxcY_oA01zmidP4HUhtzUVsSIuU91_QooMXina41hNl4pfjKfcpRtggHdd9-LcfKRxSrST6SefLTxOE77dz1dOX_uk08SNuhUz8cgxmiBL4xSj9V58_uVtRE1MnM_Y4MHTPXL2Kw7FjU60BDviI-TDQqk09uTERhBeWr1EM-VJqS5H4o1YZzxBQ
ExpiredPublicLink=1a76a046-ece8-4a2d-9a5a-00b09b86e1ec
ExpiredPrivateLink=0de9b25a-6708-4e92-81a3-85a32de6315d
ExpiredLinkIDPrivate_NoAccess=0227194f-b6d6-4ed6-93de-455d6bcb4cff
ExpiredLinkIDPrivate_AllAccess=b209c2e1-cbc6-4054-b22f-af70db8cec8c
BasicRegistrationLink=FBD4BF72-E519-47EB-E04A-08DC3275B90F
ProRegistrationLink=27C32AB8-9389-4E1D-E04B-08DC3275B90F
ExpiredRegistrationLink_NoShare=C5F6E2E3-F238-406A-7278-08DC4E814562
ExpiredRegistrationLink_ExpiredShare=523C11E3-58D6-4ECF-727A-08DC4E814562
ExpiredRegistrationLink_RegisteredUser=EDF97450-EE54-4D2E-727B-08DC4E814562
PatentsShareID=967bb8c2-c8f3-46c9-99cc-9e9d520a0f64
Session=System.Net.CookieContainer
Wait=TransPerfect.Automation.Framework.Wait
Second=Seconds
Millisecond=Milliseconds
Minute=Minutes
Hour=Hours
Seconds=Seconds
Milliseconds=Milliseconds
Minutes=Minutes
Hours=Hours
"""

def create_globals(globals_str: str) -> Environment:
    """
    Parse a string of assignments (one per line) and return an Environment with those variables defined.
    Example input:
        a="foo"
        b="bar"
    """
    env = Environment()
    for line in globals_str.split('\n'):
        line = line.strip()
        if not line or '=' not in line:
            continue
        var_name, value = line.split('=', 1)
        var_name = var_name.strip()
        value = value.strip()
        # Remove surrounding quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        env.define(var_name, Type(value, "string"))
    return env
