print de.hybris.platform.jalo.type.TypeManager.getInstance().getType('$1').allSuperTypes
    .stream()
    .map { itemType -> itemType.code }
    .collect()
    .reverse()
    .join('/')
println '/$1'