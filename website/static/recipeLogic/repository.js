// SearchQuery.js
const special = "09azAZ";
const code0 = special.charCodeAt(0);
const code9 = special.charCodeAt(1);
const codea = special.charCodeAt(2);
const codez = special.charCodeAt(3);
const codeA = special.charCodeAt(4);
const codeZ = special.charCodeAt(5);
const charCount = 26 + 10;
const charOffset = 128 - charCount;
export class SearchQuery {
    constructor(text) {
        this.original = text;
        this.words = text.match(/[A-Za-z0-9@]+/g) || [];
        this.indexBits = new Int32Array(4);
        this.mod = null;
        for (var i = 0; i < this.words.length; i++) {
            var word = this.words[i];
            if (word.startsWith('@')) {
                this.mod = word.substring(1).toLowerCase();
                this.words.splice(i, 1);
                i--;
                continue;
            }
            this.words[i] = word = word.toLowerCase();
            var len = word.length;
            var c1 = 0, c2 = 0;
            for (var j = 0; j < len; j++) {
                var char = word.charCodeAt(j);
                var c0;
                if (char >= code0 && char <= code9)
                    c0 = char - code0;
                else if (char >= codea && char <= codez)
                    c0 = char - codea + 10;
                else if (char >= codeA && char <= codeZ)
                    c0 = char - codeA + 10;
                else
                    continue;
                this.SetBit(charOffset + c0);
                if (j >= 1) {
                    this.SetBit((c1 * charCount + c0) % charOffset);
                    if (j >= 2)
                        this.SetBit(((c2 * charCount + c1) * charCount + c0) % charOffset);
                }
                c2 = c1;
                c1 = c0;
            }
        }
    }
    SetBit(bitId) {
        var element = Math.trunc(bitId / 32);
        var bit = 1 << (bitId % 32);
        this.indexBits[element] |= bit;
    }
    Match(text) {
        if (text === null)
            return false;
        var textLower = text.toLowerCase();
        for (var i = 0; i < this.words.length; i++) {
            if (!textLower.includes(this.words[i]))
                return false;
        }
        return true;
    }
}
// Repository.js
const charCodeItem = "i".charCodeAt(0);
const charCodeFluid = "f".charCodeAt(0);
const charCodeRecipe = "r".charCodeAt(0);
const DATA_VERSION = 5;
export class Repository {
    constructor(data) {
        this.objects = {};
        this.objectPositionMap = {};
        this.bytes = new Uint8Array(data);
        this.elements = new Int32Array(data);
        this.view = new DataView(data);
        this.textReader = new TextDecoder();
        let dataVersion = this.elements[0];
        if (dataVersion != DATA_VERSION)
            throw new Error(`Unsupported data version: ${dataVersion} (Required: ${DATA_VERSION}). This may be caused by the browser cache. Please try reloading using F5 or Ctrl+F5.`);
        this.items = this.GetSlice(this.elements[1]);
        this.fluids = this.GetSlice(this.elements[2]);
        this.oreDicts = this.GetSlice(this.elements[3]);
        this.recipeTypes = this.GetSlice(this.elements[4]);
        this.recipes = this.GetSlice(this.elements[5]);
        this.service = this.GetSlice(this.elements[6]);
        this.FillObjectPositionMap(this.items);
        this.FillObjectPositionMap(this.fluids);
        this.FillObjectPositionMap(this.oreDicts);
        this.FillObjectPositionMap(this.recipes);
        let remap = this.ReadSlice(this.elements[7]);
        this.FillRecipesRemap(remap);
    }
    static load(data) {
        const repository = new Repository(data);
        Repository.current = repository;
        return repository;
    }
    FillRecipesRemap(remap) {
        for (let i = 0; i < remap.length; i++) {
            let remapPos = remap[i];
            let id = this.GetString(this.elements[remapPos]);
            this.objectPositionMap[id] = this.elements[remapPos + 1];
        }
    }
    FillObjectPositionMap(elements) {
        for (var i = 0; i < elements.length; i++) {
            var id = this.GetString(this.elements[elements[i] + 4]);
            this.objectPositionMap[id] = elements[i];
        }
    }
    GetById(id) {
        if (!id)
            return null;
        var idCode = id.charCodeAt(0);
        var type = idCode == charCodeItem ? Item : idCode == charCodeFluid ? Fluid : idCode == charCodeRecipe ? Recipe : OreDict;
        if (!this.objectPositionMap[id])
            return null;
        return this.GetObject(this.objectPositionMap[id], type);
    }
    ObjectMatchQueryBits(query, pointer) {
        var arr = query.indexBits;
        for (var i = 0; i < 4; i++) {
            if ((this.elements[pointer + i] & arr[i]) !== arr[i])
                return false;
        }
        return true;
    }
    GetString(pointer) {
        var _a;
        if (pointer == -1)
            return null;
        return (_a = this.objects[pointer]) !== null && _a !== void 0 ? _a : (this.objects[pointer] = this.ReadString(pointer));
    }
    ReadString(pointer) {
        var length = this.elements[pointer];
        var begin = pointer * 4 + 4;
        return this.textReader.decode(this.bytes.subarray(begin, begin + length));
    }
    GetSlice(pointer) {
        var _a;
        return (_a = this.objects[pointer]) !== null && _a !== void 0 ? _a : (this.objects[pointer] = this.ReadSlice(pointer));
    }
    ReadSlice(pointer) {
        var length = this.elements[pointer];
        return this.elements.subarray(pointer + 1, pointer + 1 + length);
    }
    GetObject(pointer, prototype) {
        var _a;
        if (pointer === -1)
            return null;
        return (_a = this.objects[pointer]) !== null && _a !== void 0 ? _a : (this.objects[pointer] = this.ReadObject(pointer, prototype));
    }
    ReadObject(pointer, prototype) {
        return new prototype(this, pointer);
    }
    GetObjectIfMatchingSearch(query, pointer, prototype) {
        if (query === null)
            return this.GetObject(pointer, prototype);
        if (!this.ObjectMatchQueryBits(query, pointer))
            return null;
        var inst = this.GetObject(pointer, prototype);
        if (query.original.length === 1)
            return inst;
        return inst.MatchSearchText(query) ? inst : null;
    }
    IsObjectMatchingSearch(obj, query) {
        if (query === null)
            return true;
        if (!this.ObjectMatchQueryBits(query, obj.objectOffset))
            return false;
        if (query.original.length === 1)
            return true;
        return obj.MatchSearchText(query);
    }
}
class MemMappedObject {
    constructor(repository, offset) {
        this.repository = repository;
        this.objectOffset = offset;
    }
    GetInt(offset) {
        return this.repository.elements[offset + this.objectOffset];
    }
    GetDouble(offset) {
        return this.repository.view.getFloat64(4 * (offset + this.objectOffset), true);
    }
    GetString(offset) {
        return this.repository.GetString(this.repository.elements[offset + this.objectOffset]);
    }
    GetSlice(offset) {
        return this.repository.GetSlice(this.repository.elements[offset + this.objectOffset]);
    }
    GetArray(offset, prototype) {
        let slice = this.GetSlice(offset);
        let result = new Array(slice.length);
        for (var i = 0; i < slice.length; i++) {
            result[i] = this.repository.GetObject(slice[i], prototype);
        }
        return result;
    }
    GetObject(offset, prototype) {
        return this.repository.GetObject(this.repository.elements[offset + this.objectOffset], prototype);
    }
}
class SearchableObject extends MemMappedObject {
    constructor() {
        super(...arguments);
        this.id = this.GetString(4);
    }
}
export class RecipeObject extends SearchableObject {
}
export class Goods extends RecipeObject {
    get name() { return this.GetString(5); }
    get mod() { return this.GetString(6); }
    get internalName() { return this.GetString(7); }
    get iconId() { return this.GetInt(9); }
    get tooltip() { return this.GetString(10); }
    get unlocalizedName() { return this.GetString(11); }
    get nbt() { return this.GetString(12); }
    get production() { return this.GetSlice(13); }
    get consumption() { return this.GetSlice(14); }
    MatchSearchText(query) {
        if (query.mod !== null && !this.mod.toLowerCase().includes(query.mod)) {
            return false;
        }
        return query.Match(this.name) || query.Match(this.tooltip);
    }
}
export class Item extends Goods {
    get stackSize() { return this.GetInt(15); }
    get damage() { return this.GetInt(16); }
    get container() { return this.GetObject(17, FluidContainer); }
    get tooltipDebugInfo() {
        var baseInfo = `${this.mod}:${this.internalName}:${this.damage}`;
        var nbt = this.nbt;
        if (nbt != null)
            baseInfo += "\n" + nbt;
        return baseInfo;
    }
}
export class FluidContainer extends MemMappedObject {
    get fluid() { return this.GetObject(0, Fluid); }
    get amount() { return this.GetInt(1); }
    get empty() { return this.GetObject(2, Item); }
}
export class Fluid extends Goods {
    get isGas() { return this.GetInt(15) === 1; }
    get containers() { return this.GetSlice(16); }
    get tooltipDebugInfo() {
        return `${this.mod}:${this.internalName}`;
    }
}
export class OreDict extends RecipeObject {
    constructor(repository, offset) {
        super(repository, offset);
        this.items = this.GetArray(5, Item);
    }
    MatchSearchText(query) {
        var items = this.items;
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            if (this.repository.ObjectMatchQueryBits(query, item.objectOffset) && item.MatchSearchText(query))
                return true;
        }
        return false;
    }
}
export class RecipeType extends MemMappedObject {
    constructor(repository, offset) {
        super(repository, offset);
        this.singleblocks = this.GetArray(5, Item);
        this.defaultCrafter = this.GetObject(6, Item);
        this.multiblocks = this.GetArray(3, Item);
    }
    get name() { return this.GetString(0); }
    get category() { return this.GetString(1); }
    get dimensions() { return this.GetSlice(2); }
    get shapeless() { return this.GetInt(4) === 1; }
}
class GtRecipe extends MemMappedObject {
    get voltage() { return this.GetInt(0); }
    get durationTicks() { return this.GetInt(1); }
    get durationSeconds() { return this.GetInt(1) / 20; }
    get durationMinutes() { return this.GetInt(1) / (20 * 60); }
    get amperage() { return this.GetInt(2); }
    get voltageTier() { return this.GetInt(3); }
    get metadata() { return this.GetArray(4, GtRecipeMetadata); }
    get circuitConflicts() { return this.GetInt(5); }
    get specialValue() { return this.GetInt(6); }
    MetadataByKey(key, defaultValue = 0) {
        for (const metadata of this.metadata) {
            if (metadata.key === key) {
                return metadata.value;
            }
        }
        return defaultValue;
    }
}
export class GtRecipeMetadata extends MemMappedObject {
    get key() { return this.GetString(0); }
    get value() { return this.GetDouble(1); }
}
export var RecipeIoType;
(function (RecipeIoType) {
    RecipeIoType[RecipeIoType["ItemInput"] = 0] = "ItemInput";
    RecipeIoType[RecipeIoType["OreDictInput"] = 1] = "OreDictInput";
    RecipeIoType[RecipeIoType["FluidInput"] = 2] = "FluidInput";
    RecipeIoType[RecipeIoType["ItemOutput"] = 3] = "ItemOutput";
    RecipeIoType[RecipeIoType["FluidOutput"] = 4] = "FluidOutput";
})(RecipeIoType || (RecipeIoType = {}));
const RecipeIoTypePrototypes = [Item, OreDict, Fluid, Item, Fluid];
export class Recipe extends SearchableObject {
    constructor() {
        super(...arguments);
        this.recipeType = this.GetObject(6, RecipeType);
    }
    get gtRecipe() { return this.GetObject(7, GtRecipe); }
    get items() { var _a; return (_a = this.computedIo) !== null && _a !== void 0 ? _a : (this.computedIo = this.ComputeItems()); }
    ComputeItems() {
        var slice = this.GetSlice(5);
        var elements = slice.length / 5;
        var result = new Array(elements);
        var index = 0;
        for (var i = 0; i < elements; i++) {
            var type = slice[index++];
            var ptr = slice[index++];
            result[i] = {
                type: type,
                goodsPtr: ptr,
                goods: this.repository.GetObject(ptr, RecipeIoTypePrototypes[type]),
                slot: slice[index++],
                amount: slice[index++],
                probability: slice[index++] / 100,
            };
        }
        return result;
    }
    MatchSearchText(query) {
        var slice = this.GetSlice(5);
        var count = slice.length / 5;
        for (var i = 0; i < count; i++) {
            var pointer = slice[i * 5 + 1];
            if (!this.repository.ObjectMatchQueryBits(query, pointer))
                continue;
            var objType = RecipeIoTypePrototypes[slice[i * 5]];
            var obj = this.repository.GetObject(pointer, objType);
            if (obj.MatchSearchText(query))
                return true;
        }
        return false;
    }
}

// index.js

// Load the atlas image
const atlas = document.createElement("img");  // new Image();
atlas.src = "https://github.com/ShadowTheAge/gtnh-data/blob/6d35153688de5ae8e02807b942099618de1d9276/atlas.webp?raw=true";
// Load repository and data in parallel
const [repositoryModule, response] = await Promise.all([
    import("./repository.js"),
    fetch(import.meta.resolve("https://github.com/ShadowTheAge/gtnh-data/raw/6d35153688de5ae8e02807b942099618de1d9276/data.bin"))
]);
const stream = response.body.pipeThrough(new DecompressionStream("gzip"));
const buffer = await new Response(stream).arrayBuffer();
repositoryModule.Repository.load(buffer);
console.log("Repository loaded", repositoryModule.Repository.current);


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/*
<!DOCTYPE html>
<html>

<body>

<p id="out2"></p>
<button onclick="startUp()">E</button>

<script>
try {

// SearchQuery.js
const special = "09azAZ";
const code0 = special.charCodeAt(0);
const code9 = special.charCodeAt(1);
const codea = special.charCodeAt(2);
const codez = special.charCodeAt(3);
const codeA = special.charCodeAt(4);
const codeZ = special.charCodeAt(5);
const charCount = 26 + 10;
const charOffset = 128 - charCount;
class SearchQuery {
    constructor(text) {
        this.original = text;
        this.words = text.match(/[A-Za-z0-9@]+/g) || [];
        this.indexBits = new Int32Array(4);
        this.mod = null;
        for (var i = 0; i < this.words.length; i++) {
            var word = this.words[i];
            if (word.startsWith('@')) {
                this.mod = word.substring(1).toLowerCase();
                this.words.splice(i, 1);
                i--;
                continue;
            }
            this.words[i] = word = word.toLowerCase();
            var len = word.length;
            var c1 = 0, c2 = 0;
            for (var j = 0; j < len; j++) {
                var char = word.charCodeAt(j);
                var c0;
                if (char >= code0 && char <= code9)
                    c0 = char - code0;
                else if (char >= codea && char <= codez)
                    c0 = char - codea + 10;
                else if (char >= codeA && char <= codeZ)
                    c0 = char - codeA + 10;
                else
                    continue;
                this.SetBit(charOffset + c0);
                if (j >= 1) {
                    this.SetBit((c1 * charCount + c0) % charOffset);
                    if (j >= 2)
                        this.SetBit(((c2 * charCount + c1) * charCount + c0) % charOffset);
                }
                c2 = c1;
                c1 = c0;
            }
        }
    }
    SetBit(bitId) {
        var element = Math.trunc(bitId / 32);
        var bit = 1 << (bitId % 32);
        this.indexBits[element] |= bit;
    }
    Match(text) {
        if (text === null)
            return false;
        var textLower = text.toLowerCase();
        for (var i = 0; i < this.words.length; i++) {
            if (!textLower.includes(this.words[i]))
                return false;
        }
        return true;
    }
}
// Repository.js
const charCodeItem = "i".charCodeAt(0);
const charCodeFluid = "f".charCodeAt(0);
const charCodeRecipe = "r".charCodeAt(0);
const DATA_VERSION = 5;
class Repository {
    constructor(data) {
        this.objects = {};
        this.objectPositionMap = {};
        this.bytes = new Uint8Array(data);
        this.elements = new Int32Array(data);
        this.view = new DataView(data);
        this.textReader = new TextDecoder();
        let dataVersion = this.elements[0];
        if (dataVersion != DATA_VERSION)
            throw new Error(`Unsupported data version: ${dataVersion} (Required: ${DATA_VERSION}). This may be caused by the browser cache. Please try reloading using F5 or Ctrl+F5.`);
        this.items = this.GetSlice(this.elements[1]);
        this.fluids = this.GetSlice(this.elements[2]);
        this.oreDicts = this.GetSlice(this.elements[3]);
        this.recipeTypes = this.GetSlice(this.elements[4]);
        this.recipes = this.GetSlice(this.elements[5]);
        this.service = this.GetSlice(this.elements[6]);
        this.FillObjectPositionMap(this.items);
        this.FillObjectPositionMap(this.fluids);
        this.FillObjectPositionMap(this.oreDicts);
        this.FillObjectPositionMap(this.recipes);
        let remap = this.ReadSlice(this.elements[7]);
        this.FillRecipesRemap(remap);
    }
    static load(data) {
        const repository = new Repository(data);
        Repository.current = repository;
        return repository;
    }
    FillRecipesRemap(remap) {
        for (let i = 0; i < remap.length; i++) {
            let remapPos = remap[i];
            let id = this.GetString(this.elements[remapPos]);
            this.objectPositionMap[id] = this.elements[remapPos + 1];
        }
    }
    FillObjectPositionMap(elements) {
        for (var i = 0; i < elements.length; i++) {
            var id = this.GetString(this.elements[elements[i] + 4]);
            this.objectPositionMap[id] = elements[i];
        }
    }
    GetById(id) {
        if (!id)
            return null;
        var idCode = id.charCodeAt(0);
        var type = idCode == charCodeItem ? Item : idCode == charCodeFluid ? Fluid : idCode == charCodeRecipe ? Recipe : OreDict;
        if (!this.objectPositionMap[id])
            return null;
        return this.GetObject(this.objectPositionMap[id], type);
    }
    ObjectMatchQueryBits(query, pointer) {
        var arr = query.indexBits;
        for (var i = 0; i < 4; i++) {
            if ((this.elements[pointer + i] & arr[i]) !== arr[i])
                return false;
        }
        return true;
    }
    GetString(pointer) {
        var _a;
        if (pointer == -1)
            return null;
        return (_a = this.objects[pointer]) !== null && _a !== void 0 ? _a : (this.objects[pointer] = this.ReadString(pointer));
    }
    ReadString(pointer) {
        var length = this.elements[pointer];
        var begin = pointer * 4 + 4;
        return this.textReader.decode(this.bytes.subarray(begin, begin + length));
    }
    GetSlice(pointer) {
        var _a;
        return (_a = this.objects[pointer]) !== null && _a !== void 0 ? _a : (this.objects[pointer] = this.ReadSlice(pointer));
    }
    ReadSlice(pointer) {
        var length = this.elements[pointer];
        return this.elements.subarray(pointer + 1, pointer + 1 + length);
    }
    GetObject(pointer, prototype) {
        var _a;
        if (pointer === -1)
            return null;
        return (_a = this.objects[pointer]) !== null && _a !== void 0 ? _a : (this.objects[pointer] = this.ReadObject(pointer, prototype));
    }
    ReadObject(pointer, prototype) {
        return new prototype(this, pointer);
    }
    GetObjectIfMatchingSearch(query, pointer, prototype) {
        if (query === null)
            return this.GetObject(pointer, prototype);
        if (!this.ObjectMatchQueryBits(query, pointer))
            return null;
        var inst = this.GetObject(pointer, prototype);
        if (query.original.length === 1)
            return inst;
        return inst.MatchSearchText(query) ? inst : null;
    }
    IsObjectMatchingSearch(obj, query) {
        if (query === null)
            return true;
        if (!this.ObjectMatchQueryBits(query, obj.objectOffset))
            return false;
        if (query.original.length === 1)
            return true;
        return obj.MatchSearchText(query);
    }
}
class MemMappedObject {
    constructor(repository, offset) {
        this.repository = repository;
        this.objectOffset = offset;
    }
    GetInt(offset) {
        return this.repository.elements[offset + this.objectOffset];
    }
    GetDouble(offset) {
        return this.repository.view.getFloat64(4 * (offset + this.objectOffset), true);
    }
    GetString(offset) {
        return this.repository.GetString(this.repository.elements[offset + this.objectOffset]);
    }
    GetSlice(offset) {
        return this.repository.GetSlice(this.repository.elements[offset + this.objectOffset]);
    }
    GetArray(offset, prototype) {
        let slice = this.GetSlice(offset);
        let result = new Array(slice.length);
        for (var i = 0; i < slice.length; i++) {
            result[i] = this.repository.GetObject(slice[i], prototype);
        }
        return result;
    }
    GetObject(offset, prototype) {
        return this.repository.GetObject(this.repository.elements[offset + this.objectOffset], prototype);
    }
}
class SearchableObject extends MemMappedObject {
    constructor() {
        super(...arguments);
        this.id = this.GetString(4);
    }
}
class RecipeObject extends SearchableObject {
}
class Goods extends RecipeObject {
    get name() { return this.GetString(5); }
    get mod() { return this.GetString(6); }
    get internalName() { return this.GetString(7); }
    get iconId() { return this.GetInt(9); }
    get tooltip() { return this.GetString(10); }
    get unlocalizedName() { return this.GetString(11); }
    get nbt() { return this.GetString(12); }
    get production() { return this.GetSlice(13); }
    get consumption() { return this.GetSlice(14); }
    MatchSearchText(query) {
        if (query.mod !== null && !this.mod.toLowerCase().includes(query.mod)) {
            return false;
        }
        return query.Match(this.name) || query.Match(this.tooltip);
    }
}
class Item extends Goods {
    get stackSize() { return this.GetInt(15); }
    get damage() { return this.GetInt(16); }
    get container() { return this.GetObject(17, FluidContainer); }
    get tooltipDebugInfo() {
        var baseInfo = `${this.mod}:${this.internalName}:${this.damage}`;
        var nbt = this.nbt;
        if (nbt != null)
            baseInfo += "\n" + nbt;
        return baseInfo;
    }
}
class FluidContainer extends MemMappedObject {
    get fluid() { return this.GetObject(0, Fluid); }
    get amount() { return this.GetInt(1); }
    get empty() { return this.GetObject(2, Item); }
}
class Fluid extends Goods {
    get isGas() { return this.GetInt(15) === 1; }
    get containers() { return this.GetSlice(16); }
    get tooltipDebugInfo() {
        return `${this.mod}:${this.internalName}`;
    }
}
class OreDict extends RecipeObject {
    constructor(repository, offset) {
        super(repository, offset);
        this.items = this.GetArray(5, Item);
    }
    MatchSearchText(query) {
        var items = this.items;
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            if (this.repository.ObjectMatchQueryBits(query, item.objectOffset) && item.MatchSearchText(query))
                return true;
        }
        return false;
    }
}
class RecipeType extends MemMappedObject {
    constructor(repository, offset) {
        super(repository, offset);
        this.singleblocks = this.GetArray(5, Item);
        this.defaultCrafter = this.GetObject(6, Item);
        this.multiblocks = this.GetArray(3, Item);
    }
    get name() { return this.GetString(0); }
    get category() { return this.GetString(1); }
    get dimensions() { return this.GetSlice(2); }
    get shapeless() { return this.GetInt(4) === 1; }
}
class GtRecipe extends MemMappedObject {
    get voltage() { return this.GetInt(0); }
    get durationTicks() { return this.GetInt(1); }
    get durationSeconds() { return this.GetInt(1) / 20; }
    get durationMinutes() { return this.GetInt(1) / (20 * 60); }
    get amperage() { return this.GetInt(2); }
    get voltageTier() { return this.GetInt(3); }
    get metadata() { return this.GetArray(4, GtRecipeMetadata); }
    get circuitConflicts() { return this.GetInt(5); }
    get specialValue() { return this.GetInt(6); }
    MetadataByKey(key, defaultValue = 0) {
        for (const metadata of this.metadata) {
            if (metadata.key === key) {
                return metadata.value;
            }
        }
        return defaultValue;
    }
}
class GtRecipeMetadata extends MemMappedObject {
    get key() { return this.GetString(0); }
    get value() { return this.GetDouble(1); }
}
var RecipeIoType;
(function (RecipeIoType) {
    RecipeIoType[RecipeIoType["ItemInput"] = 0] = "ItemInput";
    RecipeIoType[RecipeIoType["OreDictInput"] = 1] = "OreDictInput";
    RecipeIoType[RecipeIoType["FluidInput"] = 2] = "FluidInput";
    RecipeIoType[RecipeIoType["ItemOutput"] = 3] = "ItemOutput";
    RecipeIoType[RecipeIoType["FluidOutput"] = 4] = "FluidOutput";
})(RecipeIoType || (RecipeIoType = {}));
const RecipeIoTypePrototypes = [Item, OreDict, Fluid, Item, Fluid];
class Recipe extends SearchableObject {
    constructor() {
        super(...arguments);
        this.recipeType = this.GetObject(6, RecipeType);
    }
    get gtRecipe() { return this.GetObject(7, GtRecipe); }
    get items() { var _a; return (_a = this.computedIo) !== null && _a !== void 0 ? _a : (this.computedIo = this.ComputeItems()); }
    ComputeItems() {
        var slice = this.GetSlice(5);
        var elements = slice.length / 5;
        var result = new Array(elements);
        var index = 0;
        for (var i = 0; i < elements; i++) {
            var type = slice[index++];
            var ptr = slice[index++];
            result[i] = {
                type: type,
                goodsPtr: ptr,
                goods: this.repository.GetObject(ptr, RecipeIoTypePrototypes[type]),
                slot: slice[index++],
                amount: slice[index++],
                probability: slice[index++] / 100,
            };
        }
        return result;
    }
    MatchSearchText(query) {
        var slice = this.GetSlice(5);
        var count = slice.length / 5;
        for (var i = 0; i < count; i++) {
            var pointer = slice[i * 5 + 1];
            if (!this.repository.ObjectMatchQueryBits(query, pointer))
                continue;
            var objType = RecipeIoTypePrototypes[slice[i * 5]];
            var obj = this.repository.GetObject(pointer, objType);
            if (obj.MatchSearchText(query))
                return true;
        }
        return false;
    }
}

// index.js

function startUp() {
// Load the atlas image
const atlas = document.createElement("img");  // new Image();
atlas.src = "https://github.com/ShadowTheAge/gtnh-data/blob/6d35153688de5ae8e02807b942099618de1d9276/atlas.webp?raw=true";
// Load repository and data in parallel
const [repositoryModule, response] = await Promise.all([
    import("./repository.js"),
    fetch(import.meta.resolve("https://github.com/ShadowTheAge/gtnh-data/raw/6d35153688de5ae8e02807b942099618de1d9276/data.bin"))
]);
const stream = response.body.pipeThrough(new DecompressionStream("gzip"));
const buffer = await new Response(stream).arrayBuffer();
repositoryModule.Repository.load(buffer);
document.getElementById("out2").innerHTML = "Repository loaded", repositoryModule.Repository.current;
}

} catch (err) {
document.getElementById("out2").innerHTML = "Error ";
}
document.getElementById("out2").innerHTML += "  done";
</script>

</body>

</html>
*/