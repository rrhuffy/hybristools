// xg $PROJECTS_DIR/hybristools/groovy/compareItemStagedAndOnline.groovy --parameters Product code EA_3022543 $'\36' | unroll_pk - | multiline_tabulate - 12345 --csv-delimiter=$'\36' -gt

// TODO: wait for --group in multiline_tabulate to compare items in collections regardless of order

// TODO: in case of:
// Cannot find exactly one Item with type Product with code = 8738210332 in both Staged (2) and Online version (2)
// catalogVersionService.setSessionCatalogVersions(flexibleSearchService.search("select {cv.pk} from {CatalogVersion as cv join Catalog as c on {cv.catalog}={c.pk} and {c.id}='ProductCatalog'}").result)

separator = '$4'
blacklist = ['itemModelContext', 'tenantId', 'class']

type = "$1"
qualifier = "$2"
value = "$3"

stagedItems = flexibleSearchService.search("select {i.pk} from {$type as i join CatalogVersion as cv on {i.catalogVersion}={cv.pk} } where {i.$qualifier}='$value' and {cv.version}='Staged'").result
onlineItems = flexibleSearchService.search("select {i.pk} from {$type as i join CatalogVersion as cv on {i.catalogVersion}={cv.pk} } where {i.$qualifier}='$value' and {cv.version}='Online'").result

if (stagedItems.size() != 1 || onlineItems.size() != 1) {
    println "Cannot find exactly one Item with type $type with $qualifier = $value in both Staged (${stagedItems.size()}) and Online version (${onlineItems.size()})"
    return
}

printBothItems(stagedItems[0], onlineItems[0])

def isFieldBlacklisted(fieldName) {
    return blacklist.contains(fieldName)
}

def cleanTextForPrint(textToClean) {
    maxSizeToPrint = 4096
    totalSize = textToClean.size()
    if (totalSize > maxSizeToPrint) {
        postfixIfTooLong = "...(total: $totalSize)..."
        textToClean = textToClean.take(maxSizeToPrint - postfixIfTooLong.size()) + postfixIfTooLong
    }
    textToClean = textToClean.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return textToClean
}

def unrollField(fieldName, fieldValue) {
    if (fieldName.equals("catalogVersion")) {
        return "${fieldValue.catalog.id}/${fieldValue.version}"
    }
    return fieldValue
}

def shouldUseThisField(fieldValue) {
    if (fieldValue == null)
        return false

    if (fieldValue instanceof String && fieldValue.equals("")) {
        return false
    }

    if (fieldValue instanceof java.util.Collection && fieldValue.size() == 0) {
        return false
    }

    if (fieldValue instanceof java.util.Map && fieldValue.size() == 0) {
        return false
    }

    return true
}

def getFieldNameFromMethod(method) {
    fieldNameBig = method.name.replace('get', '')
    fieldName = fieldNameBig[0].toLowerCase() + fieldNameBig.substring(1)
    return fieldName
}

def printSingleFieldValueIfNeeded(fieldName, fieldValueStaged, fieldValueOnline, locale = null) {
    if (!shouldUseThisField(fieldValueStaged) && !shouldUseThisField(fieldValueOnline))
        return

    safeTextValueStaged = cleanTextForPrint(unrollField(fieldName, fieldValueStaged).toString())
    safeTextValueOnline = cleanTextForPrint(unrollField(fieldName, fieldValueOnline).toString())

    if (locale != null) {
        println "$fieldName[$locale]$separator${safeTextValueStaged}$separator${safeTextValueOnline}"
    } else {
        println "$fieldName$separator${safeTextValueStaged}$separator${safeTextValueOnline}"
    }
}

def printBothItems(itemStaged, itemOnline) {
    localizedFields = []
    nonlocalizedFields = []

    itemStaged.metaClass.methods.each { method -> 
        // find only getters
        if (method.name.startsWith("get")) {
            fieldName = getFieldNameFromMethod(method)

            if (isFieldBlacklisted(fieldName)) {
                return
            }

            if (method.parameterTypes.size() == 0) {
                // this doesn't have any parameters (looking for parameter-less methods with name "get*")
                valueStaged = method.invoke(itemStaged, null)
                valueOnline = method.invoke(itemOnline, null)
                if (shouldUseThisField(valueStaged) || shouldUseThisField(valueOnline)) {
                    nonlocalizedFields.add([fieldName, valueStaged, valueOnline])
                }
            } else if (method.parameterTypes.size() == 1 && method.parameterTypes[0].getTheClass() == java.util.Locale.class) {
                // Locale is the only parameter then it is localized field
                defaultLocalizationService.getSupportedDataLocales().each { locale ->
                    valueStaged = method.invoke(itemStaged, locale)
                    valueOnline = method.invoke(itemOnline, locale)
                    if (shouldUseThisField(valueStaged) || shouldUseThisField(valueOnline)) {
                        localizedFields.add([fieldName, valueStaged, valueOnline, locale])
                    }
                }
            }
        }
    }

    // remove nonlocalized fields if we found any localized versions of them (using reverse iterator to remove )
    for (int i=nonlocalizedFields.size()-1; i>=0; i--) {
        for (int j=localizedFields.size()-1; j>=0; j--) {
            if (nonlocalizedFields[i][0] == localizedFields[j][0] && nonlocalizedFields[i][1] == localizedFields[j][1]) {
                // println "DEBUG: Removing '${nonlocalizedFields[i][0]}' because found '${localizedFields[j][0]}[${localizedFields[j][2]}]' and both contains the same value: '${nonlocalizedFields[i][1]}'"
                nonlocalizedFields.remove(i)
                break // no need to search through localizedFields anymore in this loop (then go to next nonlocalizedFields element)
            }
        }
    }

    // sort nonlocalized fields alphabetically by first value (fieldName), but show common fields first
    ordering = new OrderBy([
        {it[0] != 'pk'},
        {it[0] != 'itemtype'},
        {it[0] != 'uid'},
        {it[0] != 'code'},
        {it[0] != 'creationtime'},
        {it[0] != 'modifiedtime'},
        {it[0] != 'catalogVersion'},
        {it[0]}])
    nonlocalizedFields.sort(ordering)

    // sort localized fields alphabetically by third value (locale), then first value (fieldName)
    // or just use sort { it[0] } to sort by first value (fieldName)
    localizedFields.sort { a, b -> a[2].toString() <=> b[2].toString() ?: a[0] <=> b[0] } 
    
    // print nonlocalized fields
    nonlocalizedFields.each {
        printSingleFieldValueIfNeeded(*it)
    }

    // print localized fields
    localizedFields.each {
        printSingleFieldValueIfNeeded(*it)
    }

}

null // avoid printing output and result when using execute_script.py