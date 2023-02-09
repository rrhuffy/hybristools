flexibleSearchService.search("select {pk} from {BusinessProcess} where {code}='yourBusinessProcess'").result.each { bp ->
    bp.emails = new java.util.ArrayList();
    modelService.save(bp)
    businessProcessService.restartProcess(bp, 'generateNotificationEmail')
}