// xg $PROJECTS_DIR/hybristools/groovy/addDotStarToCMSSite.groovy
cmsSites = flexibleSearchService.search("select {pk} from {CMSSite}").result
if (cmsSites.size() > 1) {
    println "More than one CMSSite found, exiting without changes"
    return
}
cmsSite = cmsSites[0]
oldPatterns = cmsSite.getUrlPatterns()
if (!oldPatterns.contains(".*")) { 
    newPatterns = new ArrayList<>(oldPatterns)
    newPatterns.add(".*")
    cmsSite.setUrlPatterns(newPatterns)
    modelService.save(cmsSite)
}
null // avoid printing output and result when using execute_script.py