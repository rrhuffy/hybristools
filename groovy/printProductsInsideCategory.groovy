// xg $PROJECTS_DIR/hybristools/groovy/printProductsInsideCategory.groovy --parameters 106 | treepywithoutcolor
// WARNING! Replacing all "/" into "\", because "/" is used by treepywithoutcolor as a separator

categoryCode = '$1'

def getItemName(item) {
    // first try default locale for name, if it is not set then try en, then pl and then pl_PL locales
    name = item.getName()
    name = name != null ? name : item.getName(new Locale('en'))
    name = name != null ? name : item.getName(new Locale('pl'))
    // if pl_PL is available then also try it
    if (defaultLocalizationService.getSupportedDataLocales().any { it.toString() == "pl_PL" } ) {
        name = name != null ? name : item.getName(new Locale('pl_PL'))
    }
    // escape all slashes to backslashes, so output won't be messed because of slashed in localized product name
    return name?.replace('/', '\\') ?: ''
}

def printCategoriesWithProductsRecursively(item, previousPath='') {
    name = getItemName(item)
    codeWithName = "[${item.code}]($name)"

    // must use def explicitly to avoid reusing old value inside recursive calls
    def pathWithCodeAndName = previousPath != '' ? "$previousPath/$codeWithName" : codeWithName
    if (item.getCategories().size() == 0) {
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
    } else {
        item.getCategories().each { printCategoriesWithProductsRecursively(it, pathWithCodeAndName) }
    }
}

category = flexibleSearchService.search("SELECT {pk} FROM {Category} WHERE {code} = '$categoryCode'").result[0]
printCategoriesWithProductsRecursively(category)
null // avoid printing output and result when using execute_script.py