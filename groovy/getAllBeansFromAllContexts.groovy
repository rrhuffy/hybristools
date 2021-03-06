// to print all beans from all contexts:
// xg $PROJECTS_DIR/hybristools/groovy/getAllBeansFromAllContexts.groovy
// to search for authenticationManager in results:
// xg $PROJECTS_DIR/hybristools/groovy/getAllBeansFromAllContexts.groovy | grep authenticationManager
import de.hybris.platform.spring.HybrisContextLoaderListener
import org.springframework.web.context.ContextLoader
import org.springframework.web.context.WebApplicationContext

field = ContextLoader.getDeclaredField("currentContextPerThread")
field.setAccessible(true)
allContexts = field.get(HybrisContextLoaderListener)
allContexts.each { key, value ->
    value.beanFactory.beanDefinitionNames.each { bean ->
        println "${key.getContextName()}/${bean}"
    }
}
null // avoid printing output and result when using execute_script.py
