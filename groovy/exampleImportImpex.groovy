// xg $PROJECTS_DIR/hybristools/groovy/exampleImportImpex.groovy --parameters 'UPDATE B2BCustomer; uid[unique=true]; password\n;mark.rivers@rustic-hw.com;12341234'

impexToImport = '''$1'''
if (impexToImport.equals('$' + '1')) {
    println "You must provide 1 argument: impex"
    return
}

importImpex(impexToImport)

def importImpex(String content) {
    mediaRes = new de.hybris.platform.servicelayer.impex.impl.StreamBasedImpExResource(
        new ByteArrayInputStream(content.getBytes()),
        de.hybris.platform.util.CSVConstants.HYBRIS_ENCODING)
    importService.importData(mediaRes)
}

null // avoid printing output and result when using execute_script.py