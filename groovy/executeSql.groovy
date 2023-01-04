// xg $PROJECTS_DIR/hybristools/groovy/executeSql.groovy --parameters "update cmssite set p_active = true where p_uid ='poland'"
// xg $g/executeSql.groovy --parameters "update cmssite set p_active = true where p_uid ='poland'"

sqlToExecute = '''$1'''
if (sqlToExecute.equals('$' + '1')) {
    println 'You must provide 1 argument: sqlToExecute'
    return
}

connection = de.hybris.platform.core.Registry.getCurrentTenant().getDataSource().getConnection();
statement = connection.createStatement();

try {
    statement.execute(sqlToExecute);
    println "Success"
} catch (Exception e) {
    println "Error: $e"
}

de.hybris.platform.util.Utilities.tryToCloseJDBC(connection, statement, null)

// clear all possible caches (first one is needed for sure, remaining ones may depend on implementation)
de.hybris.platform.core.Registry.getCurrentTenant().getCache().clear()
cacheRegionProvider.getRegions().each { it.clearCache() }
net.sf.ehcache.CacheManager.ALL_CACHE_MANAGERS.each { it.clearAll() }

null // avoid printing output and result when using execute_script.py
