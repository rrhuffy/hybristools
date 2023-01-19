// xg $PROJECTS_DIR/hybristools/groovy/getCurrentBearerToken.groovy

token = flexibleSearchService.search("SELECT {pk} FROM {OAuthAccessToken} order by {modifiedTime} desc").result[0]
println token == null ? "null" : oauthTokenStore.deserializeAccessToken(token.getToken())
