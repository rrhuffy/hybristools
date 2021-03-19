// xg $PROJECTS_DIR/hybristools/groovy/printProductCategoriesRecursively.groovy --parameters 3881061 | treepywithoutcolor
// WARNING! Replacing all "/" into "\", because "/" is used by treepywithoutcolor as a separator

def getItemName(item) {
    // first try default locale for name, if it is not set then try en, then pl and then pl_PL locales
    name = item.getName()
    name = name != null ? name : item.getName(new Locale('en'))

    // if pl is available then try it
    pl = defaultLocalizationService.getSupportedDataLocales().find { it.toString() == "pl" }
    if (pl != null) {
        name = name != null ? name : item.getName(pl)
    }

    // if pl_PL is available then try it
    pl_PL = defaultLocalizationService.getSupportedDataLocales().find { it.toString() == "pl_PL" }
    if (pl_PL != null) {
        name = name != null ? name : item.getName(pl_PL)
    }
    return name
}

def printCategoriesRecursively(item, previous='') {
    name = getItemName(item)
    itemClassWithoutModelSuffix = item.getClass().getSimpleName().replace('Model', '')
    codeWithName = "[$itemClassWithoutModelSuffix](code)${item.code} <$name> {${item.catalogVersion.version}}"
    fixedCodeWithName = codeWithName.replace('/', '\\')
    def toPrint = previous == '' ? fixedCodeWithName : "$previous/$fixedCodeWithName"
    if (item.getSupercategories().size() == 0) {
        println toPrint
    } else {
        item.getSupercategories().each { printCategoriesRecursively(it, toPrint) }
    }
}

productCode = '''$1'''
if (productCode.equals('$' + '1')) {
    println "You must provide 1 argument: product code"
    return
}

products = flexibleSearchService.search("SELECT {pk} FROM {Product} WHERE {code} = '$productCode'").result
products = products.findAll { !it.hasProperty('catalogVersion') || it.catalogVersion.version != 'Staged' }
printCategoriesRecursively(products[0])
null // avoid printing output and result when using execute_script.py