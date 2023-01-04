// xg $PROJECTS_DIR/hybristools/groovy/getCronJobLogs.groovy --parameters 000044X7
// xg $g/getCronJobLogs.groovy --parameters 000044X7

cronJobCode = '''$1'''
if (cronJobCode.equals('$' + '1')) {
    println 'You must provide 1 argument: cronJob code'
    return
}

cronJob = flexibleSearchService.search("select {pk} from {CronJob} where {code}='$cronJobCode'").result[0]
if (cronJob == null) {
    println "Cannot find CronJob with code $cronJobCode"
    return
}

cronJob.logFiles.takeRight(5).each { logFileModel ->
    mediaService.getFiles(logFileModel).each {
    println "$logFileModel -> ${logFileModel.getCreationtime()}"
        def zipFile = new java.util.zip.ZipFile(it)
        zipFile.entries().each {
            println zipFile.getInputStream(it).text
        }
    }
}

null // avoid printing output and result when using execute_script.py
