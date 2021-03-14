// xg $PROJECTS_DIR/hybristools/groovy/exampleRunQueryInAllLocales.groovy --parameters M25687

codeToSearch = '''$1'''
if (codeToSearch.equals('$' + '1')) {
    println "You must provide 1 argument: Product code"
    return
}

productQueryString =
"""
    select {pk}
    from {
        Product as p
        JOIN CatalogVersion AS cv ON {cv.pk} = {p.catalogVersion}
        JOIN Catalog AS c ON {c.pk} = {cv.catalog}
    }
    where
        {code}=?code
        and {cv.version}='Online'
"""

productQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(productQueryString)
productQuery.setCount(1);
productQuery.addQueryParameter("code", codeToSearch)
product = flexibleSearchService.search(productQuery).getResult().get(0)

localizedNameFromProductQueryString =
"""
    select {name}
    from {Product}
    where {pk}=?pk
"""
localizedNameFromProductQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(localizedNameFromProductQueryString);
localizedNameFromProductQuery.addQueryParameter("pk", product.getPk())
localizedNameFromProductQuery.setResultClassList([String])

defaultLocalizationService.getSupportedDataLocales().each { locale ->
    localizedNameFromProductQuery.setLocale(locale)
    print "Trying locale: ${locale.toString().padLeft(5)}: "
    localizedNameFromProductResult = flexibleSearchService.search(localizedNameFromProductQuery).result
    println "Result: ${localizedNameFromProductResult}"
}

// if you want to read any item's localized field based on field name as string then instead of using reflection you can use:
// product.getPersistenceContext().getLocalizedValue(fieldName, locale);

null // avoid printing output and result when using execute_script.py