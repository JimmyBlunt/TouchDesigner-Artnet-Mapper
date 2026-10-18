"""Run inside TD: path-only migration, preserving active shaders and material values."""
import ast, copy, hashlib, importlib, json
from pathlib import Path
from pixelblaze_mapper import material_paths, material_library, material_texture_runtime
for module in (material_paths, material_library, material_texture_runtime):
    importlib.reload(module)
root = Path(project.folder)
library = op('/project1/madmapper_library')
browser = op('/project1/material_browser')
router = op('/project1/multi_controller_output')
assert not router.op('artnet_510_sender_callbacks').module.status()['enabled']
catalog = root / 'material_library/catalogs/madmapper-official-d7ff211.json'
digest = lambda text: hashlib.sha256(text.encode('utf-8')).hexdigest()
catalog_hash = hashlib.sha256(catalog.read_bytes()).hexdigest()
protected_paths = ['/project1/show_control/'+name for name in ('show_json','automation_json','imported_json')]
protected_paths += [router.path+'/'+name for name in ('controller_config','segment_config')]
protected_paths += [n.path for n in op('/project1').findChildren() if isinstance(n,textDAT) and any(token in n.name.lower() for token in ('shader','frag','vertex','pixel'))]
protected_text = {path:digest(op(path).text) for path in protected_paths}
custom_pars = {owner.path:{p.name:str(p.eval()) for p in owner.customPars} for owner in (library,browser,op('/project1/madmapper_material_player'),op('/project1/material_gradient_player'))}
state_text = library.op('browser_state').text
parameter_document = json.loads(json.dumps(library.op('runtime').module.PARAMETER_STORE.to_dict()))

def builder_runtime(filename):
    tree = ast.parse((root/'pixelblaze_mapper'/filename).read_text(encoding='utf-8'))
    factory = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_runtime_source')
    scope = {}
    exec(compile(ast.Module(body=[factory],type_ignores=[]),filename,'exec'),scope)
    return scope['_runtime_source']()

def replace_functions(dat, source, names):
    replacements = {n.name:ast.get_source_segment(source,n) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in names}
    assert set(replacements)==set(names)
    old = dat.text
    lines = old.splitlines(keepends=True)
    nodes = [n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(nodes)==len(names)
    for node in sorted(nodes,key=lambda n:n.lineno,reverse=True):
        lines[node.lineno-1:node.end_lineno] = [replacements[node.name]+'\n']
    updated = ''.join(lines)
    compile(updated,dat.path,'exec')
    dat.text = updated

replace_functions(library.op('runtime'),builder_runtime('build_material_library_browser.py'),('_load_direct','_validated_file'))
replace_functions(browser.op('unified_runtime'),builder_runtime('build_unified_material_browser.py'),('_imported_items',))
library.par.Catalogfile.expr = "project.folder + '/material_library/catalogs/madmapper-official-d7ff211.json'"
library.par.Importroot.expr = "project.folder + '/material_library/imported'"
library.par.Approvedroots.expr = 'project.folder'
assert library.op('runtime').module.refresh(reset_page=False)
assert browser.op('unified_runtime').module.refresh(reset_page=False)
# Module initialization may create defaults for visible preview cards. Keep the
# complete pre-install parameter document, including values not yet persisted.
from pixelblaze_mapper.imported_material_state import ImportedMaterialStateStore
library.op('runtime').module.PARAMETER_STORE = ImportedMaterialStateStore.from_dict(parameter_document)
library.store('madmapper_parameter_store',copy.deepcopy(parameter_document))
patched_files = []
for node in op('/project1').findChildren():
    par = getattr(node.par,'file',None)
    if par is None:
        continue
    value = str(par.eval())
    if '/material_library/' not in value.replace('\\','/').lower():
        continue
    resolved = Path(material_paths.resolve_asset_path(value,project_root=root))
    assert resolved.exists(), str(resolved)
    par.expr = 'project.folder + '+repr('/'+resolved.relative_to(root).as_posix())
    patched_files.append(node.path)
document = material_paths.load_catalog_document(catalog)
missing = [entry['id'] for entry in document['materials'] if any(entry.get(key) and not Path(entry[key]).is_file() for key in ('source_path','preview_path'))]
excluded = {'Catalogfile','Importroot','Approvedroots'}
checks = {
    'catalog_bytes_preserved':hashlib.sha256(catalog.read_bytes()).hexdigest()==catalog_hash,
    'all_638_assets_resolve':len(document['materials'])==638 and not missing,
    'shader_and_show_sources_preserved':all(digest(op(path).text)==value for path,value in protected_text.items()),
    'material_parameters_preserved':all(str(op(path).par[name].eval())==value for path,values in custom_pars.items() for name,value in values.items() if name not in excluded),
    'stored_material_values_preserved':parameter_document==json.loads(json.dumps(library.op('runtime').module.PARAMETER_STORE.to_dict())),
    'browser_selection_preserved':state_text==library.op('browser_state').text,
    'output_off':not router.op('artnet_510_sender_callbacks').module.status()['enabled'],
}
evidence = {'checks':checks,'catalog_sha256':catalog_hash,'records':len(document['materials']),'missing':missing,'resolved_source_root':document['source']['root'],'portable_file_nodes':patched_files,'protected_source_count':len(protected_text)}
(root/'docs/release-v1.0.0/qa/material-portability-live.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'records':len(document['materials']),'portable_file_count':len(patched_files)}))
assert all(checks.values()), checks
