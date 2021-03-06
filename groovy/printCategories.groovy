// xg $PROJECTS_DIR/hybristools/groovy/printCategories.groovy | treepywithoutcolor

def getItemName(item) {
    // first try default locale for name, if it is not set then try en, then pl and then pl_PL locales
    name = item.getName()
    if (name != null) {
        return name
    }

    supportedLocales = defaultLocalizationService.getSupportedDataLocales()
    desiredLocales = ['en', 'pl', 'pl_PL']
    desiredLocales.each { locale ->
        if (locale in supportedLocales) {
            nameInThisLocale = item.getName(locale)
            if (nameInThisLocale != null) {
                return nameInThisLocale
            }
        }
    }

    return '' // fallback when cannot find name in given locales
}

def printCategoriesWithProductsRecursively(item, previousPath='')
{
    name = getItemName(item)
    codeWithName = "[${item.code}]($name)"

    // must use def explicitly to avoid reusing old value inside recursive calls
    def pathWithCodeAndName = previousPath != '' ? "$previousPath/$codeWithName" : codeWithName
    if (item.getCategories().size() == 0)
    {
        // if we have any product inside category then print products
        if (item.getProducts().size() > 0) {
            item.getProducts().each {
                // escape all slashes to backslashes, so output won't be messed because of slashed in localized product name
                escapedName = it?.getName()?.replace('/', '\\') ?: ''
                println "$pathWithCodeAndName/${it.getCode()} $escapedName"
            }
        } else {  // if we haven't any product inside category then print category
            println pathWithCodeAndName
        }
    }
    else
    {
        item.getCategories().each { printCategoriesWithProductsRecursively(it, pathWithCodeAndName) }
    }
}

flexibleSearchService.search("SELECT {pk} FROM {Category}").result.each { category ->
    if (category.getAllSupercategories().size() == 0) {
        printCategoriesWithProductsRecursively(category)
    }
}
null // avoid printing output and result when using execute_script.py