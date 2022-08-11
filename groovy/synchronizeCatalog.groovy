// xg $PROJECTS_DIR/hybristools/groovy/synchronizeCatalog.groovy --parameters powertools

syncJobs = flexibleSearchService.search("select {pk} from {CatalogVersionSyncJob} where {code} like '%$1%'").result
if (syncJobs.size() > 1) {
    println "More than one CatalogVersionSyncJob found, exiting. All jobs:\n${syncJobs.code.join('\n')}"
    return
}
catalogVersionSyncJobModel = syncJobs[0]

catalogVersionSyncJob = modelService.getSource(catalogVersionSyncJobModel)
cronJob = catalogVersionSyncJob.newExecution()
syncItemCronJobModel = modelService.get(cronJob.getPK())
syncItemCronJobModel.setForceUpdate(false)
syncItemCronJobModel.setCreateSavedValues(false)
syncItemCronJobModel.setLogToDatabase(false)
syncItemCronJobModel.setLogToFile(false)
syncItemCronJobModel.setLogLevelDatabase(de.hybris.platform.cronjob.enums.JobLogLevel.WARNING)
syncItemCronJobModel.setLogLevelFile(de.hybris.platform.cronjob.enums.JobLogLevel.INFO)
syncItemCronJobModel.setErrorMode(de.hybris.platform.cronjob.enums.ErrorMode.FAIL)
syncItemCronJobModel.setFullSync(true)
syncItemCronJobModel.setAbortOnCollidingSync(false)
syncItemCronJobModel.setRemoveOnExit(true)

if (de.hybris.platform.util.Config.getBoolean("task.engine.loadonstartup", false)) {
    trigger = modelService.create(de.hybris.platform.cronjob.model.TriggerModel.class)
    // de.hybris.platform.cronjob.jalo.CronJobManager#prepareTriggerTaskAttributes
    // triggerTaskMap.put("executionTimeMillis", trigger.getActivationTime().getTime() + TimeUnit.SECONDS.toMillis(10L));
    // that's why we have -10 seconds here, so it will be executed immediately
    trigger.setActivationTime(new java.util.Date(java.lang.System.currentTimeMillis()-10*1000))
    trigger.setCronJob(syncItemCronJobModel)
    syncItemCronJobModel.setTriggers(java.util.Collections.singletonList(trigger))
    modelService.save(trigger)
    println "CronJob's (${syncItemCronJobModel.getPk()}) trigger should activate soon, to check if it is completed:"
    println "xg 'cronJobService.getCronJob(\"${syncItemCronJobModel.getCode()}\").getStatus()'"
    if (de.hybris.platform.util.Config.getInt("task.polling.interval.min", 0) > 1 ||
        de.hybris.platform.util.Config.getInt("task.polling.interval", 0) > 1 || (
            !de.hybris.platform.util.Config.getString("task.auxiliaryTables.scheduler.interval.seconds", "*").contains("*")) &&
            de.hybris.platform.util.Config.getInt("task.auxiliaryTables.scheduler.interval.seconds", 0) > 1
        ) {
        println "To speed up trigger activation locally to one second you can set in local.properties:"
        println "task.polling.interval.min=1\ntask.polling.interval=1\ntask.auxiliaryTables.scheduler.interval.seconds=1"
    }
} else {
    println "Cannot run cronjob automatically, because 'task.engine.loadonstartup' is false"
    println "TODO: figure out why it's not working when created and started from groovy, as a workaround run this manually:"
    println "xg 'cronJobService.performCronJob(cronJobService.getCronJob(\"${syncItemCronJobModel.getCode()}\"))'"
    println "To check if it is completed:"
    println "xg 'cronJobService.getCronJob(\"${syncItemCronJobModel.getCode()}\").getStatus()'"
}

modelService.save(syncItemCronJobModel)
