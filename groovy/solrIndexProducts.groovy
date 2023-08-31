// xg $PROJECTS_DIR/hybristools/groovy/solrIndexProducts.groovy --parameters ProductIndex 8796290678785
// xg $PROJECTS_DIR/hybristools/groovy/solrIndexProducts.groovy --parameters ProductIndex 8796290678785,8796093186649

firstArgument = '''$1'''
secondArgument = '''$2'''
if (firstArgument.equals('$' + '1') || secondArgument.equals('$' + '2') ) {
    println "You must provide 2 arguments: index and productCodeInCsv. Examples: '--parameters ProductIndex 8796290678785', '--parameters ProductIndex 8796290678785,8796093186649'"
    return
}

solrFacetSearchConfigs = flexibleSearchService.search("select {pk} from {SolrFacetSearchConfig} where {name} like '%$firstArgument%'").result
if (solrFacetSearchConfigs.size() > 1) {
    println "More than one SolrFacetSearchConfig found, exiting. All configs:\n${solrFacetSearchConfigs.name.join('\n')}"
    return
}

sqlCompatibleProductPKs = secondArgument.split(',').collect{"'$it'"}.join(",")
println "sqlCompatibleProductPKs: $sqlCompatibleProductPKs"

products = flexibleSearchService.search("select {pk} from {Product} where {pk} in (${sqlCompatibleProductPKs})").result
println "products: $products"

solrFacetSearchConfig = solrFacetSearchConfigs[0]
solrIndexerHotUpdateJob = flexibleSearchService.search("select {pk} from {ServicelayerJob} where {code}='solrIndexerHotUpdateJob'").result[0]

updateCronJob = modelService.create(de.hybris.platform.solrfacetsearch.model.indexer.cron.SolrIndexerHotUpdateCronJobModel)
updateCronJob.setFacetSearchConfig(solrFacetSearchConfig)
updateCronJob.setJob(solrIndexerHotUpdateJob)
updateCronJob.setIndexTypeName("Product")
updateCronJob.setItems(products)
updateCronJob.setRemoveOnExit(true)

if (de.hybris.platform.util.Config.getBoolean("task.engine.loadonstartup", false)) {
    trigger = modelService.create(de.hybris.platform.cronjob.model.TriggerModel.class)
    // de.hybris.platform.cronjob.jalo.CronJobManager#prepareTriggerTaskAttributes
    // triggerTaskMap.put("executionTimeMillis", trigger.getActivationTime().getTime() + TimeUnit.SECONDS.toMillis(10L));
    // that's why we have -10 seconds here, so it will be executed immediately
    trigger.setActivationTime(new java.util.Date(java.lang.System.currentTimeMillis()-10*1000))
    trigger.setCronJob(updateCronJob)
    updateCronJob.setTriggers(java.util.Collections.singletonList(trigger))
    modelService.save(trigger)
    println "CronJob's (${updateCronJob.getPk()}) trigger should activate soon, to check if it is completed:"
    println "xg 'cronJobService.getCronJob(\"${updateCronJob.getCode()}\").getStatus()'"
    if (Eval.me(de.hybris.platform.util.Config.getString("task.polling.interval.min", "999")) > 1 ||
        Eval.me(de.hybris.platform.util.Config.getString("task.polling.interval", "999")) > 1 ||
        Eval.me(de.hybris.platform.util.Config.getString("task.auxiliaryTables.scheduler.interval.seconds", "999")) > 1) {
        println "To speed up trigger activation locally to one second you can set in local.properties:"
        println "task.polling.interval.min=1\ntask.polling.interval=1\ntask.auxiliaryTables.scheduler.interval.seconds=1"
    }
} else {
    println "Cannot run cronjob automatically, because 'task.engine.loadonstartup' is false"
    println "TODO: figure out why it's not working when created and started from groovy, as a workaround run this manually:"
    println "xg 'cronJobService.performCronJob(cronJobService.getCronJob(\"${updateCronJob.getCode()}\"))'"
    println "To check if it is completed:"
    println "xg 'cronJobService.getCronJob(\"${updateCronJob.getCode()}\").getStatus()'"
    println "'CronJob with code ${updateCronJob.getCode()} not found' means execution is done and cronjob is removed due to setRemoveOnExit(true)"
}

modelService.save(updateCronJob)

null // avoid printing output and result when using execute_script.py
