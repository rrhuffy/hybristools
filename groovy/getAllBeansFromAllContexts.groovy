/*
to print all beans from all contexts:
xg $PROJECTS_DIR/hybristools/groovy/getAllBeansFromAllContexts.groovy
to search for authenticationManager in results:
xg $PROJECTS_DIR/hybristools/groovy/getAllBeansFromAllContexts.groovy | grep authenticationManager
*/
import org.springframework.web.context.ContextLoader
import org.springframework.web.context.WebApplicationContext

field = ContextLoader.getDeclaredField("currentContextPerThread")
field.setAccessible(true)
classLoaderToWebApplicationContextMap = field.get(de.hybris.platform.spring.HybrisContextLoaderListener)
classLoaderToWebApplicationContextMap.each { classLoader, context ->
    context.beanFactory.beanDefinitionNames.each { bean ->
        println "${classLoader.getContextName()}/${bean}"
    }
}
null // avoid printing output and result when using execute_script.py
