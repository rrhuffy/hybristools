separator = '$4'
blacklist = ['itemModelContext', 'tenantId', 'class', 'sealed', 'type']

def getItemsInOnlineIfPossible(type, qualifier, value, maxReturnedItems=3) {
    originalResult = flexibleSearchService.search("select {pk} from {$type} where {$qualifier}='$value'").result

    // if there is only one result then return it without any filtering
    if (originalResult.size() < 2) {
        return originalResult
    }

    // TODO: use filtering in showItemOnline.groovy + showItemStaged.groovy and let this file handle both of them
//     println "WARN: No [Online] filtering, returning all products!"; return originalResult

    // if item has "catalogVersion" attribute then remove ones with Staged version
    filteredResult = originalResult.findAll{ !it.hasProperty('catalogVersion') || it.catalogVersion.version != 'Staged' }
    if (filteredResult.size() > 1 && filteredResult.size() < 5) {
        println "WARN: ${filteredResult.size()} elements found after filtering out Staged ones (from all ${originalResult.size()}), printing all of them:"
    } else if (filteredResult.size() > 5) {
        println "WARN: ${filteredResult.size()} elements found after filtering out Staged ones (from all ${originalResult.size()}), printing first $maxReturnedItems of them:"
        filteredResult = filteredResult[0..maxReturnedItems-1]
    }
    // println "DEBUG: Filtered results from ${originalResult.size()} to ${filteredResult.size()}"
    return filteredResult
}

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
    fieldNameBig = method.name.replaceFirst("^get", "").replaceFirst("^is", "")
    fieldName = fieldNameBig[0].toLowerCase() + fieldNameBig.substring(1)
    return fieldName
}

def printSingleFieldValueIfNeeded(fieldName, fieldValue, locale = null, separator) {
    if (!shouldUseThisField(fieldValue) )
        return

    fieldValue = unrollField(fieldName, fieldValue)
    safeTextValue = cleanTextForPrint(fieldValue.toString())
    if (fieldValue instanceof java.util.Collection) {
        fieldName = fieldName + "(${fieldValue.size()})"
    }

    if (locale != null) {
        println "$fieldName[$locale]$separator${safeTextValue}"
    } else {
        println "$fieldName$separator${safeTextValue}"
    }
}

def getItemsReferencingThisOne(item) {
    // try MySQL way first
    try {
        sourceTypeAndQualifierQueryString = "select {t.code}, {ad.qualifier} from {AttributeDescriptor AS ad JOIN Type AS fieldType ON {ad.attributeType} = {fieldType.PK} JOIN Type AS t ON {ad.EnclosingType} = {t.PK}} where {fieldType.code}='ContentSlot' and {t.code}!='ContentSlot' and {ad.modifiers}&256=256"
        sourceTypeAndQualifierQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(sourceTypeAndQualifierQueryString)
        sourceTypeAndQualifierQuery.setResultClassList([String,String])
        results = flexibleSearchService.search(sourceTypeAndQualifierQuery).result
    } catch (de.hybris.platform.servicelayer.search.exceptions.FlexibleSearchException e) {
        // in case of exception try HSQLDB
        sourceTypeAndQualifierQueryString = "select {t.code}, {ad.qualifier} from {AttributeDescriptor AS ad JOIN Type AS fieldType ON {ad.attributeType} = {fieldType.PK} JOIN Type AS t ON {ad.EnclosingType} = {t.PK}} where {fieldType.code}='ContentSlot' and {t.code}!='ContentSlot' and BITAND({ad.modifiers},256)>0"
        sourceTypeAndQualifierQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(sourceTypeAndQualifierQueryString)
        sourceTypeAndQualifierQuery.setResultClassList([String,String])
        results = flexibleSearchService.search(sourceTypeAndQualifierQuery).result
    }

    results.each { type, qualifier ->
        flexibleSearchService.search("select {pk} from {$type} where {$qualifier}='${item.pk}'").result.each { referencingProduct ->
            println "${type}->$qualifier$separator${referencingProduct.pk}"
        }
    }
}

def printEverythingForThisItem(item) {
    localizedFields = []
    nonlocalizedFields = []
    for (org.codehaus.groovy.reflection.CachedMethod method: item.metaClass.methods) {
        // find only getters
        if (method.name.startsWith("get") || method.name.startsWith("is")) {
            fieldName = getFieldNameFromMethod(method)

            if (isFieldBlacklisted(fieldName)) {
                continue
            }

            if (method.parameterTypes.size() == 0) {
                // this doesn't have any parameters (looking for parameter-less methods with name "get*" or "is*")
                value = tryToInvoke(method, item, null)
                if (shouldUseThisField(value)) {
                    nonlocalizedFields.add([fieldName, value])
                }
            } else if (method.parameterTypes.size() == 1 && method.parameterTypes[0].getTheClass() == java.util.Locale.class) {
                // Locale is the only parameter then it is localized field
                defaultLocalizationService.getSupportedDataLocales().each { locale ->
                    value = tryToInvoke(method, item, locale)
                    if (shouldUseThisField(value)) {
                        localizedFields.add([fieldName, value, locale])
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
    localizedFields.sort { a, b -> a[2].toString() <=> b[2].toString() ?: a[0] <=> b[0] }
    // localizedFields.sort { it[0] } // just sort by first value (fieldName)

    // print nonlocalized fields
    nonlocalizedFields.each {
        printSingleFieldValueIfNeeded(*it, separator)
    }

    // print localized fields
    localizedFields.each {
        printSingleFieldValueIfNeeded(*it, separator)
    }

    getItemsReferencingThisOne(item)
}

def tryToInvoke(method, item, locale) {
    try {
        return method.invoke(item, locale)
    } catch (java.lang.Exception e) {
        println "WARN: Caught $e when called ${method.name}"
        return "[$e]"
    }
}

items = getItemsInOnlineIfPossible("$1", "$2", "$3")
if (items.size() == 0) {
    println "Cannot find type $1 with $2 = $3"
    return
}

for (int i=0; i<items.size(); i++) {
    if (i != 0) {
        println "----------$separator----------"
    }
    printEverythingForThisItem(items[i])
}

null // avoid printing output and result when using execute_script.py