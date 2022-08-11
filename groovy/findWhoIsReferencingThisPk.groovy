/*
xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters 8796093057183 | multiline_tabulate -
while inotifywait -qe modify "$PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy"; do echo && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters 8796093057183 | multiline_tabulate -; done;

TODO: hide duplicated PKs, in example below there should be only Employee result
xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {UserGroup} where {uid}='admingroup'" -A --data) | grep -E "$(xf "select {pk} from {Principal} where {uid}='admin'" -A --data | paste -sd '|' -)"
PrincipalGroupRelation.source   8796093054980   PrincipalGroupRelation.target   8796093054981
Principal.pk    8796093054980   Principal.allGroups     8796093054981
User.pk 8796093054980   User.allGroups  8796093054981
Employee.pk     8796093054980   Employee.allGroups      8796093054981
Link.source     8796093054980   Link.target     8796093054981

TODO: split into query generation and execution parts, then print (to logs) completion percentage (otherwise we won't know how long we need to wait for results on server with huge database)

Works with:
normal fields
enum fields
many to many relation fields
one to many relation fields
many to one relation fields
CollectionType fields
localized fields
Jalo/Dynamic fields, but slowly, because fields of this type aren't accessible via Flexible Search it's done by querying all items having jalo/dynamic field with searched type then executing jalo/dynamic getters in each item on groovy side. Beware that queries for types with multiple candidates (many items are referencing given Type with their jalo/dynamic fields) like Media are slow (up to 30s), because they are iterating through hundreds of items and executing jalo/dynamic logic, then checking if searched pk exist in results

Normal field test
PK            | firstType             | qualifier       | fieldType       | extension       | U | L | E | D | J | O | R | C
8796771123287 | SolrFacetSearchConfig | solrIndexConfig | SolrIndexConfig | solrfacetsearch | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
echo "Expecting: " && xf "select {pk} from {SolrFacetSearchConfig} where {name}='Solr Config for Backoffice'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {solrIndexConfig} from {SolrFacetSearchConfig} where {name}='Solr Config for Backoffice'" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {solrIndexConfig} from {SolrFacetSearchConfig} where {name}='Solr Config for Backoffice'" -A --data)

Jalo/Dynamic field test (but not CollectionType, which is also tested)
PK            | firstType    | qualifier     | fieldType            | extension | U | L | E | D | J | O | R | C
8796660301911 | AbstractPage | displayStatus | CmsItemDisplayStatus | cms2      | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 1
echo "Expecting: " && xf "select {pk} from {ContentPage} where {uid}='homepage' and {catalogVersion} in ({{ select {pk} from {CatalogVersion} where {version}='Online' }})" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {pk} from {CmsItemDisplayStatus} where {code}='READY_TO_SYNC'" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {CmsItemDisplayStatus} where {code}='READY_TO_SYNC'" -A --data) | grep -E $(xf "select {pk} from {ContentPage} where {uid}='homepage' and {catalogVersion} in ({{ select {pk} from {CatalogVersion} where {version}='Online' }})" -A --data | paste -sd '|' -)

Enum field test
PK            | firstType        | qualifier | fieldType       | extension       | U | L | E | D | J | O | R | C
8796758376535 | SolrServerConfig | mode      | SolrServerModes | solrfacetsearch | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
hsi Type code SolrServerModes -A
pk       | 8796131688530
itemtype | EnumerationMetaType
echo "Expecting: " && xf "select {pk} from {SolrServerConfig} where {name}='Default'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {mode} from {SolrServerConfig} where {name}='Default'" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {mode} from {SolrServerConfig} where {name}='Default'" -A --data) | grep -E "$(xf "select {pk} from {SolrServerConfig} where {name}='Default'" -A --data | paste -sd '|' -)"

Many to many relation test
PK            | firstType | qualifier | fieldType                         | extension | U | L | E | D | J | O | R | C
8796104589399 | Principal | syncJobs  | SyncItemJob2PrincipalsyncJobsColl | catalog   | 0 | 0 | 1 | 0 | 0 | 1 | 1 | *
PK            | firstType   | qualifier          | fieldType                               | extension | U | L | E | D | J | O | R | C
8796304900183 | SyncItemJob | syncPrincipals     | SyncItemJob2PrincipalsyncPrincipalsColl | catalog   | 0 | 0 | 1 | 0 | 0 | 1 | 1 | *
echo "Expecting: " && xf "select {pk} from {UserGroup} where {uid}='cmsmanagergroup'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {pk} from {SyncItemJob} where {code}='sync powertoolsContentCatalog:Staged->Online'" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {SyncItemJob} where {code}='sync powertoolsContentCatalog:Staged->Online'" -A --data) | grep $(xf "select {pk} from {UserGroup} where {uid}='cmsmanagergroup'" -A --data)

CollectionType test 1 (non jalo/dynamic)
PK            | firstType                  | qualifier             | fieldType                | extension      | U | L | E | D | J | O | R | C
8796596306007 | ProductReferencesComponent | productReferenceTypes | productReferenceTypeList | acceleratorcms | 0 | 0 | 1 | 0 | 0 | 1 | 0 | *
echo "Expecting: " && xf "select {pk} from {ProductReferencesComponent} where {uid}='CrossSelling'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {pk} from {ProductReferenceTypeEnum} where {code}='CROSSELLING'" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {ProductReferenceTypeEnum} where {code}='CROSSELLING'" -A --data) | grep -E "$(xf "select {pk} from {ProductReferencesComponent} where {uid}='CrossSelling'" -A --data | paste -sd '|' -)"

CollectionType test 2 (non jalo/dynamic)
PK            | firstType     | qualifier    | fieldType             | extension           | U | L | E | D | J | O | R | C
8796847276119 | SiteMapConfig | siteMapPages | SiteMapPageCollection | acceleratorservices | 0 | 0 | 1 | 0 | 0 | 1 | 0 | *
echo "Expecting: " && xf "select {pk} from {SiteMapConfig} where {configid}='powertoolsSiteMapConfig'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {pk} from {SiteMapPage} where {code}=({{select {pk} from {SiteMapPageEnum} where {code}='Homepage'}})" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {SiteMapPage} where {code}=({{select {pk} from {SiteMapPageEnum} where {code}='Homepage'}})" -A --data) | grep -E "$(xf "select {pk} from {SiteMapConfig} where {configid}='powertoolsSiteMapConfig'" -A --data | paste -sd '|' -)"

CollectionType test 3 (jalo/dynamic)
PK            | firstType | qualifier | fieldType         | extension  | U | L | E | D | J | O | R | C
8796101738583 | Principal | allGroups | PrincipalGroupSet | core       | 0 | 0 | 0 | 1 | 0 | 1 | 0 | *
echo "Expecting: " && xf "select {pk} from {Principal} where {uid}='admin'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {pk} from {UserGroup} where {uid}='admingroup'" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {UserGroup} where {uid}='admingroup'" -A --data) | grep -E "$(xf "select {pk} from {Principal} where {uid}='admin'" -A --data | paste -sd '|' -)"

CollectionType test 4 (jalo/dynamic)
PK            | firstType    | qualifier    | fieldType        | extension | U | L | E | D | J | O | R | C
8796660531287 | AbstractPage | contentSlots | PageContentSlots | cms2      | 0 | 0 | 0 | 0 | 1 | 1 | 0 | *
<collectiontype code="PageContentSlots" elementtype="ContentSlotForPage" autocreate="true" generate="true" type="list" />
PK            | firstType          | qualifier | fieldType    | extension | U | L | E | D | J | O | R | C
8796684320855 | ContentSlotForPage | page      | AbstractPage | cms2      | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
echo "Expecting one of: " && xf "select {pk} from {AbstractPage} where {uid}='faq'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {pk} from {ContentSlotForPage} where {uid}='Section2A-FAQ'" 1 -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {ContentSlotForPage} where {uid}='Section2A-FAQ'" 1 -A --data) | grep -E "$(xf "select {pk} from {AbstractPage} where {uid}='faq'" -A --data | paste -sd '|' -)"

One to many test (with searched item on "one" side)
<relation code="Country2RegionRelation" generate="true" localized="false" autocreate="true">
<sourceElement type="Country" qualifier="country" cardinality="one">
<targetElement type="Region" qualifier="regions" cardinality="many">
PK            | firstType | qualifier | fieldType | extension | U | L | E | D | J | O | R | C
8796095348823 | Region    | country   | Country   | core      | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 1
PK            | firstType | qualifier | fieldType                         | extension | U | L | E | D | J | O | R | C
8796095316055 | Country   | regions   | Country2RegionRelationregionsColl | core      | 0 | 0 | 1 | 0 | 0 | 1 | 1 | *
echo "Expecting: " && xf "select {pk} from {Region} where {isocode}='US-AK'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {pk} from {Country} where {isocode}='US'" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {Country} where {isocode}='US'" -A --data) | grep -E "$(xf "select {pk} from {Region} where {isocode}='US-AK'" -A --data | paste -sd '|' -)"

Many to one reference (many items referencing one item and we are searching item on "many" side)
PK            | firstType             | qualifier        | fieldType                                                 | extension       | U | L | E | D | J | O | R | C
8796771549271 | SolrFacetSearchConfig | solrIndexedTypes | SolrFacetSearchConfig2SolrIndexedTypesolrIndexedTypesColl | solrfacetsearch | 0 | 0 | 1 | 0 | 0 | 1 | 1 | *
PK            | firstType       | qualifier                 | fieldType             | extension       | U | L | E | D | J | O | R | C
8796753821783 | SolrIndexedType | solrFacetSearchConfig     | SolrFacetSearchConfig | solrfacetsearch | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 1
Unfortunately simple search using Flexible Search won't show us that SolrFacetSearchConfig has solrIndexedTypes with many SolrIndexedType, because the reference is persisted on SolrIndexedType side.
That's why for this type of relation we will first check "what many to one relations do our type has?", then find all items on the other side and these will be items with reference to our original item.
The other way to implement this is to find RelationMetaType by sourceType/targetType, then check jalo sourceTypeCardinality/targetTypeCardinality and use sourceAttribute/targetAttribute to build a query.
echo "Expecting: " && xf "select {pk} from {SolrFacetSearchConfig} where {name}='Solr Config for Backoffice'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {pk} from {SolrIndexedType} where {identifier}='BackofficeProduct'" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {SolrIndexedType} where {identifier}='BackofficeProduct'" -A --data) | grep -E "$(xf "select {pk} from {SolrFacetSearchConfig} where {name}='Solr Config for Backoffice'" -A --data | paste -sd '|' -)"

Localized fields test
PK            | firstType        | qualifier | fieldType               | extension | U | L | E | D | J | O | R | C
8796253290583 | RendererTemplate | content   | localized:TemplateMedia | commons   | 0 | 1 | 1 | 0 | 0 | 1 | 0 | 1
echo "Expecting: " && xf "select {pk} from {RendererTemplate} where {code}='DefaultCronJobFinishNotificationTemplate'" -A --data && echo "To be found when searching who is referencing item with PK: " && xf "select {pk} from {CatalogUnawareMedia} where {code}='DefaultCronJobFinishNotificationTemplate_en'" -A --data && echo "Got: " && xg $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters $(xf "select {pk} from {CatalogUnawareMedia} where {code}='DefaultCronJobFinishNotificationTemplate_en'" -A --data) | grep -E "$(xf "select {pk} from {RendererTemplate} where {code}='DefaultCronJobFinishNotificationTemplate'" -A --data | paste -sd '|' -)"
*/

DEBUG = 0
PRINT_TO_LOGS = 0
USE_JALO_AND_DYNAMIC_HANDLER = 0 // this handler is slow, because it is not using Flexible Search queries, it calls getters on groovy side instead
MAX_TIME_SPENT_IN_JALO_AND_DYNAMIC_HANDLER_IN_MS = 1 * 1000
abortedJaloOrDynamicHandlerChecksDueToTimeSpentRestrictions = []
TYPE_BLACKLIST = ["ItemSyncTimestamp", "ModifiedCatalogItemsView", "ItemTargetVersionView", "ItemSourceVersionView"] as Set

pkToSearchAsString = '''$1'''
if (pkToSearchAsString.equals('$' + '1')) {
    println "You must provide 1 argument: PK to search"
    return
}

def debug(message) {
    if (DEBUG) {
        println "DEBUG: $message"
    }
    if (PRINT_TO_LOGS) {
        org.apache.log4j.Logger.getLogger(de.hybris.platform.servicelayer.internal.jalo.ScriptingJob).info("DEBUG: $message")
    }
}

def info(message) {
    if (PRINT_TO_LOGS) {
        org.apache.log4j.Logger.getLogger(de.hybris.platform.servicelayer.internal.jalo.ScriptingJob).info(message)
    }
    println message
}

pkToSearchAsPK = new de.hybris.platform.core.PK(Long.parseLong(pkToSearchAsString))
pkToSearchAsModel = modelService.get(pkToSearchAsPK)
if (de.hybris.platform.core.HybrisEnumValue.class.isAssignableFrom(pkToSearchAsModel.class)) {
    // special case: EnumValue
    typeToSearchAsString = modelService.getSourceTypeFromModel(pkToSearchAsModel)
} else {
    // normal case
    typeToSearchAsString = pkToSearchAsModel.itemtype
}

debug "PK: $pkToSearchAsString is of type: $typeToSearchAsString"

typeToSearchAsComposedType = de.hybris.platform.jalo.type.TypeManager.getInstance().getType(typeToSearchAsString)
allTypesToSearch = [typeToSearchAsComposedType, *typeToSearchAsComposedType.allSuperTypes]
debug "All types to check including inherited ones: ${allTypesToSearch.collect { it.code }.join(",")}"
resultsToPrint = []

allTypesToSearch.each { currentlySearchedType ->
    debug "[${currentlySearchedType.code}]"

    // search for Items with fields of our type, then find exact one
    debug "    Normal/enum/one to many/many to many field handler"

    descriptorsQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery("""
        select
            {ad.qualifier},
            {enclosingType.code},
            {enclosingTypeType.code},
            case {modifiers} & power(2,13) when 0 then 0 else 1 end
        from {
            AttributeDescriptor as ad
            join Type as enclosingType on {ad.enclosingType} = {enclosingType.pk}
            join Type as enclosingTypeType on {enclosingType.itemtype} = {enclosingTypeType.pk}
            join Type as attributeType on {ad.attributeType} = {attributeType.pk}
        }
        where
            {attributeType.code}='${currentlySearchedType.code}'
    """)
    descriptorsQuery.setResultClassList([String,String,String,Boolean])
    descriptorsResults = flexibleSearchService.search(descriptorsQuery).result
    // TODO: addresses uses owner, so they won't be found if we filter out checking that
    descriptorsResults = descriptorsResults.findAll { qualifier, code, type, isJaloOrDynamicField -> !(currentlySearchedType.code.equals("Item") && qualifier.equals("owner")) } // filter out searches in Item.owner
    /*
        firstType | qualifier | fieldType         | extension  | U | L | E | D | J | O | R | C
        CronJob   | logFiles  | LogFileCollection | processing | 0 | 0 | 1 | 0 | 1 | 1 | 0 | *
        de.hybris.platform.cronjob.jalo.CronJob#getLogFiles
        This is using jalo to search: "select {pk} from {LogFile} where {owner}=8796093350389 order by {creationTime}"
        So Item.owner contains our searched item, but fortunately there is jalo/dynamic CollectionType handler so in this case we will find our searched pk
        TODO: check if there can be a situation, where someone is using Item.owner field, but it is not fetched in jalo/dynamic way
    */

    // filter our blacklisted entries like ItemSyncTimestamp or non-searchable Items with name *View
    descriptorsResults = descriptorsResults.findAll { qualifier, code, type, isJaloOrDynamicField -> !TYPE_BLACKLIST.contains(code) }
    descriptorsResults.each { qualifier, code, type, isJaloOrDynamicField ->
        if (isJaloOrDynamicField) {
            if (!USE_JALO_AND_DYNAMIC_HANDLER) {
                return
            }

            jaloOrDynamicQueryString = "select {pk} from {${code}}"
            debug "jaloOrDynamicQueryString: ${jaloOrDynamicQueryString}"
            try {
                jaloOrDynamicQueryResult = flexibleSearchService.search(jaloOrDynamicQueryString).result
            } catch (Exception e) {
                println "WARN: Couldn't check $code type because of $e"
                return
            }
            debug "        Checking jalo/dynamic field in: ${code}.$qualifier (iterating through ${jaloOrDynamicQueryResult.size()} items)"
            timeStart = new java.util.Date().getTime();
            for (int i=0; i<jaloOrDynamicQueryResult.size(); i++) {
                itemToCheckInGroovy = jaloOrDynamicQueryResult.get(i)
                if (new java.util.Date().getTime() - timeStart > MAX_TIME_SPENT_IN_JALO_AND_DYNAMIC_HANDLER_IN_MS) {
                    debug "            ${MAX_TIME_SPENT_IN_JALO_AND_DYNAMIC_HANDLER_IN_MS}ms passed, aborting dynamic/jalo checks"
                    abortedJaloOrDynamicHandlerChecksDueToTimeSpentRestrictions.add("${code}.$qualifier(checked ${i}/${jaloOrDynamicQueryResult.size()})")
                    break
                }
                propertyValue = itemToCheckInGroovy.getProperty(qualifier)
                if (propertyValue == null) {
                    continue
                }

                if (propertyValue instanceof Collection) {
                    propertyValue.each { collectionEntry ->
                        if (collectionEntry.pk.equals(pkToSearchAsPK)) {
                            formattedMessage = "${code}.pk\t${itemToCheckInGroovy.pk}\t${code}.$qualifier\t$pkToSearchAsString"
                            debug "            + $formattedMessage"
                            resultsToPrint.add(formattedMessage)
                        }
                    }
                } else if (de.hybris.platform.core.HybrisEnumValue.class.isAssignableFrom(propertyValue.class)) {
                    enumPk = modelService.getSource(propertyValue).PK
                    if (enumPk != null && enumPk.equals(pkToSearchAsPK)) {
                        formattedMessage = "${code}.pk\t${itemToCheckInGroovy.pk}\t${code}.$qualifier\t$pkToSearchAsString"
                        debug "            + $formattedMessage"
                        resultsToPrint.add(formattedMessage)
                    }
                } else {
                    if (propertyValue != null && propertyValue.pk.equals(pkToSearchAsPK)) {
                        formattedMessage = "${code}.pk\t${itemToCheckInGroovy.pk}\t${code}.$qualifier\t$pkToSearchAsString"
                        debug "            + $formattedMessage"
                        resultsToPrint.add(formattedMessage)
                    }
                }
            }
        } else {
            // handle many to many case - because we'd end on pk of RelationMetaType which has source or target pointing into our item, but we want "the other one"
            // second option is to get Link code which also uses source/target and we don't want to return Link pk, but alternate source/target pointing to item which holds reference
            // so if source has our item then return target and if target has our item then return source (instead of pk of immediate type used for joining many to many relations)
            if (type.equals("RelationMetaType") || code.equals("Link")) {
                if (qualifier.equals("source")) {
                    qualifierToUse = "target"
                } else if (qualifier.equals("target")) {
                    qualifierToUse = "source"
                } else {
                    info "ERROR: type: $type, code: $code, qualifier: $qualifier, it's RelationMetaType or Link but it is not using either source nor target"
                    return
                }
            } else {
                // in other (than many to many or jalo/dynamic) cases just use pk
                qualifierToUse = "pk"
            }

            regularQueryString = "select {$qualifierToUse} from {$code} where {$qualifier} = $pkToSearchAsString"
            regularQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(regularQueryString)
            regularQuery.setResultClassList([String])
            try {
                regularQueryResults = flexibleSearchService.search(regularQuery).result
                debug "        ${regularQueryResults ? '+' : '-'} \"$regularQueryString\" -> $regularQueryResults"
                // iterate over results, because there may be more than one instance of given type referencing it
                regularQueryResults.each { regularEntry ->
                    formattedMessage = "${code}.$qualifierToUse\t$regularEntry\t${code}.$qualifier\t$pkToSearchAsString"
                    resultsToPrint.add(formattedMessage)
                }
            } catch (java.lang.Exception e) {
                debug "        x \"$regularQueryString\" -> ${e.message}"
            }
        }
    }

    // search for CollectionType which hold items of our type, then search for items with our pk in their collection
    debug "    CollectionType handler"
    collectionTypeQueryString = "select {pk}, {code} from {CollectionType} where {elementType}=${currentlySearchedType.PK}"
    collectionTypeQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(collectionTypeQueryString)
    collectionTypeQuery.setResultClassList([String,String])
    collectionTypeResults = flexibleSearchService.search(collectionTypeQuery).result
    collectionTypeResults.each { collectionTypePk, collectionTypeCode ->
        debug "        Searching for items using collection $collectionTypeCode"
        descriptorsWithCollectionQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery("""
            select
                {enclosingType.code},
                {ad.qualifier},
                case {modifiers} & power(2,13) when 0 then 0 else 1 end
            from {
                AttributeDescriptor! as ad 
                join ComposedType as enclosingType on {ad.enclosingType}={enclosingType.pk} 
                join ComposedType as itemType on {ad.itemType}={itemType.pk}
            }
            where 
                {attributeType}=${collectionTypePk}
        """)
        
        descriptorsWithCollectionQuery.setResultClassList([String,String,Boolean])
        descriptorsWithCollectionResults = flexibleSearchService.search(descriptorsWithCollectionQuery).result
        descriptorsWithCollectionResults.each { typeToCheck, qualifierToCheck, isJaloOrDynamicField ->
            if (isJaloOrDynamicField) {
                if (!USE_JALO_AND_DYNAMIC_HANDLER) {
                    return
                }
                jaloOrDynamicCollectionQueryString = "select {pk} from {${typeToCheck}}"
                jaloOrDynamicCollectionQueryResult = flexibleSearchService.search(jaloOrDynamicCollectionQueryString).result
                debug "            Checking jalo/dynamic field in: ${typeToCheck}.$qualifierToCheck (iterating through ${jaloOrDynamicCollectionQueryResult.size()} items)"
                timeStart = new java.util.Date().getTime();
                for (int i=0; i<jaloOrDynamicCollectionQueryResult.size(); i++) {
                    itemToCheckInGroovy = jaloOrDynamicCollectionQueryResult.get(i)
                    if (new java.util.Date().getTime() - timeStart > MAX_TIME_SPENT_IN_JALO_AND_DYNAMIC_HANDLER_IN_MS) {
                        debug "                ${MAX_TIME_SPENT_IN_JALO_AND_DYNAMIC_HANDLER_IN_MS}ms passed, aborting dynamic/jalo checks"
                        abortedJaloOrDynamicHandlerChecksDueToTimeSpentRestrictions.add("${typeToCheck}.$qualifierToCheck(checked ${i}/${jaloOrDynamicCollectionQueryResult.size()})")
                        break
                    }
                    propertyValue = itemToCheckInGroovy.getProperty(qualifierToCheck)
                    if (propertyValue instanceof Collection) {
                        propertyValue.each { collectionEntry ->
                            if (collectionEntry.pk.equals(pkToSearchAsPK)) {
                                formattedMessage = "${typeToCheck}.pk\t${itemToCheckInGroovy.pk}\t${typeToCheck}.$qualifierToCheck\t$pkToSearchAsString"
                                debug "                + $formattedMessage"
                                resultsToPrint.add(formattedMessage)
                            }
                        }
                    } else {
                        if (propertyValue != null && propertyValue.pk.equals(pkToSearchAsPK)) {
                            formattedMessage = "${typeToCheck}.pk\t${itemToCheckInGroovy.pk}\t${typeToCheck}.$qualifierToCheck\t$pkToSearchAsString"
                            debug "                + $formattedMessage"
                            resultsToPrint.add(formattedMessage)
                        }
                    }
                }
            } else {
                regularCollectionQueryString = "select {pk} from {${typeToCheck}} where {${qualifierToCheck}} like '%${pkToSearchAsString}%'"
                regularCollectionQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(regularCollectionQueryString)
                regularCollectionQuery.setResultClassList([String])
                regularCollectionResults = flexibleSearchService.search(regularCollectionQuery).result
                debug "            ${regularCollectionResults ? '+' : '-'} \"$regularCollectionQueryString\" -> $regularCollectionResults"
                regularCollectionResults.each { collectionEntry ->
                    formattedMessage = "${typeToCheck}.pk\t$collectionEntry\t${typeToCheck}.$qualifierToCheck\t$pkToSearchAsString"
                    resultsToPrint.add(formattedMessage)
                }
            }
        }
    }

    // search using RelationDescriptor to handle many to one reference (many items referencing one item and we are searching item on "many" side)
    debug "    Many to one handler will search through own type: ${currentlySearchedType.code} for fields of relation with cardinality one"
    manyToOneDescriptorQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery("""
        select
            {qualifier},
            {attributeType.code}
        from {
            RelationDescriptor as rd 
            join ComposedType as attributeType on {rd.attributeType}={attributeType.pk}
        }
        where 
            {enclosingType}=${currentlySearchedType.PK}
            and {modifiers}&256=256
    """)
    
    manyToOneDescriptorQuery.setResultClassList([String,String])
    manyToOneDescriptorResults = flexibleSearchService.search(manyToOneDescriptorQuery).result
    manyToOneDescriptorResults.each { qualifierToCheck, typeToCheck ->
        manyToOneRelationQueryString = "select {$qualifierToCheck} from {${currentlySearchedType.code}} where {pk}=$pkToSearchAsString"
        manyToOneRelationQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(manyToOneRelationQueryString)
        manyToOneRelationQuery.setResultClassList([String])
        // for unknown reason "select {mediaContainer} from {Media} where {pk}=8796849995806" returned [null] (an collection with one null element), hence filtering null entries
        manyToOneRelationResults = flexibleSearchService.search(manyToOneRelationQuery).result.findAll { it != null }
        debug "            ${manyToOneRelationResults ? '+' : '-'} \"$manyToOneRelationQueryString\" -> $manyToOneRelationResults"
        manyToOneRelationResults.each { otherPk ->
            // TODO: $qualifierToCheck is showing qualifier of the searched Type, not Type having reference to our type
            // We need to get RelationDescriptor.relationtype which gives us RelationMetaType with sourceattribute+targetattribute, then basing on their {isSource} pick correct one and use its {qualifier}
            formattedMessage = "${typeToCheck}.pk\t$otherPk\t${typeToCheck}.$qualifierToCheck\t$pkToSearchAsString"
            resultsToPrint.add(formattedMessage)
        }
    }

    // search for localized values
    debug "    Localized field handler"
    localizedTypeQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery("select {pk}, {code} from {MapType} where {returntype}=${currentlySearchedType.PK}")
    localizedTypeQuery.setResultClassList([String,String])
    localizedTypeResults = flexibleSearchService.search(localizedTypeQuery).result
    localizedTypeResults.each { localizedTypePk, localizedTypeCode ->
        debug "        Searched item may be referenced using field with type: $localizedTypeCode ($localizedTypePk)"
        descriptorString = """
            select {ad.qualifier}, {enclosingType.code}
            from {
                AttributeDescriptor as ad
                join Type as enclosingType on {ad.enclosingType}={enclosingType.pk}
            } where {ad.attributeType}=${localizedTypePk}
        """
        descriptorQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(descriptorString)
        descriptorQuery.setResultClassList([String,String])
        descriptorResult = flexibleSearchService.search(descriptorQuery).result
        descriptorResult.each { qualifier, type ->
            debug "            Item of type: $type has a localized qualifier: $qualifier, will try to find a reference in all locales"
            regularQueryString = "select {pk} from {$type} where {$qualifier}=$pkToSearchAsString"
            regularQuery = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery(regularQueryString)
            regularQuery.setResultClassList([String])
            defaultLocalizationService.getSupportedDataLocales().each { locale ->
                regularQuery.setLocale(locale)
                regularQueryResult = flexibleSearchService.search(regularQuery).result
                regularQueryResult.each { regularEntry ->
                    formattedMessage = "${type}.pk\t$regularEntry\t${type}.$qualifier[$locale]\t$pkToSearchAsString"
                    debug "                + select {pk} from {$type} where {$qualifier[$locale]}=$pkToSearchAsString"
                    resultsToPrint.add(formattedMessage)
                }
            }
        }
    }
}

if (resultsToPrint) {
    info "Type\tpk\tqualifier\tsearchedPk"
    resultsToPrint.each {
        info it
    }
}

if (!abortedJaloOrDynamicHandlerChecksDueToTimeSpentRestrictions.isEmpty()) {
    println "WARN: Aborted ${abortedJaloOrDynamicHandlerChecksDueToTimeSpentRestrictions.size()} jalo or dynamic checks because it took more than ${MAX_TIME_SPENT_IN_JALO_AND_DYNAMIC_HANDLER_IN_MS} ms: ${abortedJaloOrDynamicHandlerChecksDueToTimeSpentRestrictions.join(',')}"
    abortedJaloOrDynamicHandlerChecksDueToTimeSpentRestrictions.each{debug it}
}

null // avoid printing output and result when using execute_script.py
