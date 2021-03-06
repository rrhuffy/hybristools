// to print list of all contexts:
// xg $PROJECTS_DIR/hybristools/groovy/getBeanFromContext.groovy
// to print list of all beans in given context:
// xg $PROJECTS_DIR/hybristools/groovy/getBeanFromContext.groovy --parameters backoffice
// to find bean in given context and print its fields and methods:
// xg $PROJECTS_DIR/hybristools/groovy/getBeanFromContext.groovy --parameters backoffice backofficeLocaleService
import de.hybris.platform.spring.HybrisContextLoaderListener
import org.springframework.web.context.ContextLoader
import org.springframework.web.context.WebApplicationContext

contextName = '''$1'''
beanName = '''$2'''

field = ContextLoader.getDeclaredField("currentContextPerThread")
field.setAccessible(true)
contexts = field.get(HybrisContextLoaderListener)

if (contextName.equals('$' + "1") && beanName.equals('$' + "2")) {
    println "You must provide 2 arguments: contextName and beanName, printing all contexts:"
    contexts.each { println it.key.getContextName() }
    return
}

def context = contexts.find { contextName.equals(it.key.getContextName()) }
if (context == null) {
    println "Cannot find context with name $contextName, printing all contexts' names:"
    contexts.each { println it.key.getContextName() }
} else {
    try {
        bean = context.value.getBean(beanName)
        println "Found $beanName:\n$bean\n\nFields:"
        bean.properties.each { println "$it.key -> $it.value" }
        println "\nMethods:"
        bean.metaClass.methods*.name.sort().unique().each { println it }
    } catch (org.springframework.beans.factory.NoSuchBeanDefinitionException exc) {
        println "Cannot find bean $beanName, printing all beans' names in context $contextName:"
        context.value.beanFactory.beanDefinitionNames.each { println it }
    }
}
null // avoid printing output and result when using execute_script.py
