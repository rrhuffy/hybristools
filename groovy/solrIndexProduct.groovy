// xg $PROJECTS_DIR/hybristools/groovy/solrIndexProduct.groovy --parameters ProductIndex 8796290678785

product = flexibleSearchService.search("select {pk} from {Product} where {pk}='$2'").result[0]

solrFacetSearchConfigs = flexibleSearchService.search("select {pk} from {SolrFacetSearchConfig} where {name} like '%$1%'").result
if (solrFacetSearchConfigs.size() > 1) {
    println "More than one SolrFacetSearchConfig found, exiting. All configs:\n${solrFacetSearchConfigs.name.join('\n')}"
    return
}
solrFacetSearchConfig = solrFacetSearchConfigs[0]
solrIndexerHotUpdateJob = flexibleSearchService.search("select {pk} from {ServicelayerJob} where {code}='solrIndexerHotUpdateJob'").result[0]

updateCronJob = modelService.create(de.hybris.platform.solrfacetsearch.model.indexer.cron.SolrIndexerHotUpdateCronJobModel)
updateCronJob.setFacetSearchConfig(solrFacetSearchConfig)
updateCronJob.setJob(solrIndexerHotUpdateJob)
updateCronJob.setIndexTypeName("Product")
updateCronJob.setItems(java.util.List.of(product))
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
    if (de.hybris.platform.util.Config.getInt("task.polling.interval.min", 0) > 1 ||
        de.hybris.platform.util.Config.getInt("task.polling.interval", 0) > 1 ||
        de.hybris.platform.util.Config.getInt("task.auxiliaryTables.scheduler.interval.seconds", 0) > 1) {
        println "To speed up trigger activation locally to one second you can set in local.properties:"
        println "task.polling.interval.min=1\ntask.polling.interval=1\ntask.auxiliaryTables.scheduler.interval.seconds=1"
    }
} else {
    println "Cannot run cronjob automatically, because 'task.engine.loadonstartup' is false"
    println "TODO: figure out why it's not working when created and started from groovy, as a workaround run this manually:"
    println "xg 'cronJobService.performCronJob(cronJobService.getCronJob(\"${updateCronJob.getCode()}\"))'"
    println "To check if it is completed:"
    println "xg 'cronJobService.getCronJob(\"${updateCronJob.getCode()}\").getStatus()'"
}

modelService.save(updateCronJob)
