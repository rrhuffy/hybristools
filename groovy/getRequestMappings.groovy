/*
to print all request mappings in given context:
xg $PROJECTS_DIR/hybristools/groovy/getRequestMappings.groovy --parameters yourStorefrontContextName | multiline_tabulate -
*/
import org.springframework.web.context.ContextLoader
import org.springframework.web.context.WebApplicationContext

contextName = '''$1'''
beanName = "org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping"

field = ContextLoader.getDeclaredField("currentContextPerThread")
field.setAccessible(true)
classLoaderToWebApplicationContextMap = field.get(de.hybris.platform.spring.HybrisContextLoaderListener)

if (contextName.equals('$' + "1")) {
    println "You must provide 1 argument: contextName, printing all contexts:"
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
        println "Pattern\tMethods\tController\tMethod"
        bean.handlerMethods.each { println "${it.key.patternsCondition}\t${it.key.methodsCondition}\t${it.value.beanType.simpleName}\t${it.value.method.name}" }
    } catch (org.springframework.beans.factory.NoSuchBeanDefinitionException exc) {
        println "Cannot find bean $beanName, printing all beans' names in context $contextName:"
        context.beanFactory.beanDefinitionNames.each { println it }
    }
}
null // avoid printing output and result when using execute_script.py
