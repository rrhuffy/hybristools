// xg $PROJECTS_DIR/hybristools/groovy/printCmsNavigationNodes.groovy --parameters powertoolsContentCatalog | treepywithoutcolor
catalogId = '''$1'''

def printChildrenRecursively(item, previousPath='') {
    uidWithName = "${item.getUid()} (${item.getName()})"
    def newPath = previousPath != '' ? "$previousPath/$uidWithName" : uidWithName
    println newPath
    item.getChildren().each { child ->
        printChildrenRecursively(child, newPath)
    }
}

rootNavigationNodes = flexibleSearchService.search("SELECT {pk} FROM {CMSNavigationNode} WHERE {uid} = 'root'").result
// filter out Staged ones
rootNavigationNodes = rootNavigationNodes.findAll { !it.hasProperty('catalogVersion') || it.catalogVersion.version != 'Staged' }
// custom catalogId
if (!catalogId.equals('$' + "1")) {
    rootNavigationNodes = rootNavigationNodes.findAll { !it.hasProperty('catalogVersion') || it.catalogVersion.catalog.id.contains(catalogId) }
}

if (rootNavigationNodes.size() > 1) {
    println "More than one root navigation node found:"
    rootNavigationNodes.each { println "${it.catalogVersion.catalog.id}" }
    println "Provide the catalog id as a parameter"
    return
}

printChildrenRecursively(rootNavigationNodes[0])
null // avoid printing output and result when using execute_script.py