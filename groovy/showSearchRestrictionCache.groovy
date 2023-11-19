// xg $PROJECTS_DIR/hybristools/groovy/showSearchRestrictionCache.groovy --parameters Currency | unroll_pk -
// watchmodifybash $PROJECTS_DIR/hybristools/groovy/showSearchRestrictionCache.groovy 'xg $PROJECTS_DIR/hybristools/groovy/showSearchRestrictionCache.groovy --parameters Currency | unroll_pk -'

// de.hybris.platform.persistence.flexiblesearch.QueryParser#getQueryKey
// return Arrays.asList(principal != null ? principal.getPK() : null, sql, this.getDynamicQueriesKey(dynamicRestrictions), failOnUnknownFields, hasLanguage, disableRestrictions, disableGroupRestrictions, FlexibleSearch.isUnionAllForTypeHierarchyEnabled());

text = '''$1'''
if (text.equals('$' + '1')) {
    println "You must provide 1 argument: textToBeIncludedInOriginalSqlStatementIgnoreCase"
    return
}

cacheCreator = new de.hybris.platform.util.SingletonCreator.Creator<Map<Object, de.hybris.platform.persistence.flexiblesearch.TranslatedQuery>>() {
    protected Map<Object, de.hybris.platform.persistence.flexiblesearch.TranslatedQuery> create() {
        Class[] argumentsClass = new Class[]{Integer.TYPE};
        Object[] argumentValues = new Object[]{de.hybris.platform.persistence.flexiblesearch.QueryParser.queryCacheSize};

        try {
            Class cacheMapDefinition = Class.forName(de.hybris.platform.util.Config.getParameter("cache.flexiblesearchquery.map"));
            java.lang.reflect.Constructor constructor = cacheMapDefinition.getConstructor(argumentsClass);
            de.hybris.platform.util.collections.CacheMap cacheMap = (de.hybris.platform.util.collections.CacheMap)constructor.newInstance(argumentValues);
            return cacheMap;
        } catch (Exception var7) {
            throw new IllegalStateException("can't initialize cache", var7);
        }
    }

    protected String getID() {
        return de.hybris.platform.core.Constants.CACHE_KEYS.TRANSLATED_QUERIES_CACHE;
    }

    protected void destroy(Map<Object, de.hybris.platform.persistence.flexiblesearch.TranslatedQuery> map) {
        map.clear();
    }
}
// Map<Object, TranslatedQuery>
de.hybris.platform.core.Registry.getCurrentTenantNoFallback().getCache().getStaticCacheContent(cacheCreator).entrySet()
.findAll{it.key[1].containsIgnoreCase(text)}
.each {
    println "\n\nPrincipal: ${it.key[0]} ${it.key[5] ? 'with disableRestrictions enabled' : ''}"
    println "Original SQL:\n${it.key[1]}"
    // println "TranslatedSQL: ${it.value.sqlTemplate}"
    // println "Values: ${it.value.valueKeys}"
    sqlWithValues = it.value.sqlTemplate
    it.value.valueKeys.each {
        sqlWithValues = sqlWithValues.replaceFirst("\\?", String.valueOf(it))
    }
    println "Translated SQL with values:\n${sqlWithValues}"
}
