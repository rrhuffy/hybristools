// xg $PROJECTS_DIR/hybristools/groovy/jsonHttpMessageConverter.groovy
body = """{
	"id": "id1",
	"email": "a@a.com",
	"country": {
	    "isocode": "isocode1",
	    "name": "name1"
	}
}"""
source = new org.springframework.xml.transform.StringSource(body)
classToUnmarshallTo = de.hybris.platform.commercewebservicescommons.dto.user.AddressWsDTO.class
unmarshaller = jsonHttpMessageConverter.createUnmarshaller(classToUnmarshallTo)
unmarshalled = unmarshaller.unmarshal(source, classToUnmarshallTo).getValue()
println "\nPrinting AddressWsDTO fields:"
unmarshalled.properties.each { println "$it.key -> $it.value" }
println "\nPrinting CountryWsDTO fields:"
unmarshalled.country.properties.each { println "$it.key -> $it.value" }
null // avoid printing output and result when using execute_script.py
