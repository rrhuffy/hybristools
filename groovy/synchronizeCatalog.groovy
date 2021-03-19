// xg $PROJECTS_DIR/hybristools/groovy/synchronizeCatalog.groovy --parameters powertools Product

import de.hybris.platform.servicelayer.search.FlexibleSearchQuery
import de.hybris.platform.catalog.synchronization.SyncConfig
import de.hybris.platform.cronjob.enums.JobLogLevel
import de.hybris.platform.cronjob.enums.ErrorMode
import de.hybris.platform.catalog.synchronization.SyncResult

query = "Select {pk} from {CatalogVersionSyncJob} where {code} = 'sync $1$2Catalog:Staged->Online'";
flexibleSearchQuery = new FlexibleSearchQuery(query)
catalogVersionSyncJobModel = flexibleSearchService.search(flexibleSearchQuery).result[0]

catalogVersionSyncJob = modelService.getSource(catalogVersionSyncJobModel)
cronJob = catalogVersionSyncJob.newExecution()
syncItemCronJobModel = modelService.get(cronJob.getPK())
syncItemCronJobModel.setForceUpdate(false);
syncItemCronJobModel.setCreateSavedValues(false);
syncItemCronJobModel.setLogToDatabase(false);
syncItemCronJobModel.setLogToFile(false);
syncItemCronJobModel.setLogLevelDatabase(JobLogLevel.WARNING);
syncItemCronJobModel.setLogLevelFile(JobLogLevel.INFO);
syncItemCronJobModel.setErrorMode(ErrorMode.FAIL);
syncItemCronJobModel.setFullSync(true);
syncItemCronJobModel.setAbortOnCollidingSync(false);
modelService.save(syncItemCronJobModel);
println "TODO: figure out why it's not working when created and started from groovy, as a workaround run this manually:"
println "xg 'cronJobService.performCronJob(cronJobService.getCronJob(\"${syncItemCronJobModel.getCode()}\"))'"
println "To check if it is completed:"
println "xg 'cronJobService.getCronJob(\"${syncItemCronJobModel.getCode()}\").getStatus()'"
