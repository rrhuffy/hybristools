/*
to print list of all contexts:
xg $PROJECTS_DIR/hybristools/groovy/getBeanFromContext.groovy
to print list of all beans in given context:
xg $PROJECTS_DIR/hybristools/groovy/getBeanFromContext.groovy --parameters backoffice
to find bean in given context and print its fields and methods:
xg $PROJECTS_DIR/hybristools/groovy/getBeanFromContext.groovy --parameters backoffice backofficeLocaleService
*/
import org.springframework.web.context.ContextLoader
import org.springframework.web.context.WebApplicationContext

contextName = '''$1'''
beanName = '''$2'''

field = ContextLoader.getDeclaredField("currentContextPerThread")
field.setAccessible(true)
classLoaderToWebApplicationContextMap = field.get(de.hybris.platform.spring.HybrisContextLoaderListener)

if (contextName.equals('$' + "1") && beanName.equals('$' + "2")) {
    println "You must provide 2 arguments: contextName and beanName, printing all contexts:"
    classLoaderToWebApplicationContextMap.each { println it.key.getContextName() }
    return
}

context = classLoaderToWebApplicationContextMap.find { contextName.equals(it.key.getContextName()) }?.getValue() ?: null
if (context == null) {
    println "Cannot find context with name $contextName, printing all contexts' names:"
    classLoaderToWebApplicationContextMap.each { println it.key.getContextName() }
} else {
    try {
        bean = context.getBean(beanName)
        println "Found $beanName:\n$bean\n\nFields:"
        // filter out "beanFactory", because it has multiple irrelevant lines
        bean.properties.findAll { it.key != "beanFactory" } .each { println "$it.key -> $it.value" }
        println "\nMethods:"
        bean.metaClass.methods*.name.sort().unique().each { println it }
    } catch (org.springframework.beans.factory.NoSuchBeanDefinitionException exc) {
        println "Cannot find bean $beanName, printing all beans' names in context $contextName:"
        context.beanFactory.beanDefinitionNames.each { println it }
    }
}
null // avoid printing output and result when using execute_script.py
