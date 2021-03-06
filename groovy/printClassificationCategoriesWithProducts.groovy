// xg $PROJECTS_DIR/hybristools/groovy/printClassificationCategoriesWithProducts.groovy --parameters PowertoolsClassification | treepywithoutcolor

classificationSystemId = '$1'

def printCategoriesWithProductsRecursively(item, previousPath='') {
    nameEn = item.getName(new Locale('EN'))
    namePl = ''
    try {
        namePl = item.getName(new Locale('pl_PL'))
    }
    catch (IllegalArgumentException e) {
        // ignore
    }
    finally {
        name = nameEn != null ? nameEn : namePl
    }

    codeWithName = "[${item.code}]_$name"

    // must use def explicitly to avoid reusing old value inside recursive calls
    def pathWithCodeAndName = previousPath != '' ? "$previousPath/$codeWithName" : codeWithName
    if (item.getAllSubcategories().size() == 0) {
        item.getProducts().each {
            // escape all slashes to backslashes, so output won't be messed because of slashed in localized product name
            escapedName = it?.getName()?.replace('/', '\\') ?: ''
            println "$pathWithCodeAndName/${it.getCode()} $escapedName"
        }
    } else {
        item.getAllSubcategories().each { printCategoriesWithProductsRecursively(it, pathWithCodeAndName) }
    }
}

classificationSystem = flexibleSearchService.search(
        "SELECT {pk} FROM {ClassificationSystem} WHERE {id} = '$classificationSystemId'").result[0]
allRootCategories = [*classificationSystem.getRootCategories()]
classificationSystemVersions = classificationSystem.getCatalogVersions()
classificationSystemVersions.each {
    allRootCategories.addAll(it.getRootCategories())
}

allRootCategories.each { rootCategory ->
    rootCategory.getAllSubcategories().each { subcategory ->
        printCategoriesWithProductsRecursively(subcategory)
    }
}

null // avoid printing output and result when using execute_script.py