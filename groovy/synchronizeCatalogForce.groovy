// xg $PROJECTS_DIR/hybristools/groovy/synchronizeCatalog.groovy --parameters powertools

import de.hybris.platform.servicelayer.search.FlexibleSearchQuery
import de.hybris.platform.catalog.synchronization.SyncConfig
import de.hybris.platform.cronjob.enums.JobLogLevel
import de.hybris.platform.cronjob.enums.ErrorMode
import de.hybris.platform.catalog.synchronization.SyncResult

query = "select {pk} from {CatalogVersionSyncJob} where {code} like '%$1%'";
flexibleSearchQuery = new FlexibleSearchQuery(query)
result = flexibleSearchService.search(flexibleSearchQuery).result
if (result.size() > 1) {
    println "More than one CatalogVersionSyncJob found, exiting. All jobs:\n${result.code.join('\n')}"
    return
}
catalogVersionSyncJobModel = result[0]

catalogVersionSyncJob = modelService.getSource(catalogVersionSyncJobModel)
cronJob = catalogVersionSyncJob.newExecution()
syncItemCronJobModel = modelService.get(cronJob.getPK())
syncItemCronJobModel.setForceUpdate(true);
syncItemCronJobModel.setCreateSavedValues(false);
syncItemCronJobModel.setLogToDatabase(false);
syncItemCronJobModel.setLogToFile(false);
syncItemCronJobModel.setLogLevelDatabase(JobLogLevel.WARNING);
syncItemCronJobModel.setLogLevelFile(JobLogLevel.INFO);
syncItemCronJobModel.setErrorMode(ErrorMode.FAIL);
syncItemCronJobModel.setFullSync(true);
syncItemCronJobModel.setAbortOnCollidingSync(false);
modelService.save(syncItemCronJobModel);

if (de.hybris.platform.util.Config.getBoolean("task.engine.loadonstartup", false)) {
    trigger = modelService.create(de.hybris.platform.cronjob.model.TriggerModel.class)
    trigger.setSecond(0);
    trigger.setMinute(0);
    trigger.setHour(0);
    trigger.setDay(0);
    trigger.setMonth(0);
    trigger.setYear(0);
    trigger.setActivationTime(new java.util.Date(java.lang.System.currentTimeMillis()+0*1000))
    trigger.setCronJob(syncItemCronJobModel)
    syncItemCronJobModel.setTriggers(java.util.Collections.singletonList(trigger))
    modelService.save(trigger)
    modelService.save(syncItemCronJobModel)
    println "CronJob's (${syncItemCronJobModel.getPk()}) trigger should activate soon, to check if it is completed:"
    println "xg 'cronJobService.getCronJob(\"${syncItemCronJobModel.getCode()}\").getStatus()'"
} else {
    println "Cannot run cronjob automatically, because task.engine.loadonstartup is false"
    println "TODO: figure out why it's not working when created and started from groovy, as a workaround run this manually:"
    println "xg 'cronJobService.performCronJob(cronJobService.getCronJob(\"${syncItemCronJobModel.getCode()}\"))'"
    println "To check if it is completed:"
    println "xg 'cronJobService.getCronJob(\"${syncItemCronJobModel.getCode()}\").getStatus()'"
}
