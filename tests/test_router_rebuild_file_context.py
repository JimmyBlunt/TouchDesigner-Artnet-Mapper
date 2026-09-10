import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


class RouterRebuildContextTests(unittest.TestCase):
    def test_dat_context_does_not_replace_the_builder_file_location(self):
        source=Path(__file__).resolve().parents[1]/'pixelblaze_mapper/build_multi_controller_output.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        factory=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_ui_callbacks_source')
        scope={'LOCAL_ROOT':str(source.parents[1]),'__file__':str(source)}
        exec(compile(ast.Module(body=[factory],type_ignores=[]),str(source),'exec'),scope)
        callback=ast.parse(scope['_ui_callbacks_source']())
        rebuild=next(n for n in callback.body if isinstance(n,ast.FunctionDef) and n.name=='_rebuild_router')
        with TemporaryDirectory() as temporary:
            builder=Path(temporary)/'builder.py'
            builder.write_text("observed.append((__file__, __name__))")
            observed=[]
            globals_={'BUILDER':str(builder),'__file__':'/project1/router/ui_callbacks','observed':observed}
            exec(compile(ast.Module(body=[rebuild],type_ignores=[]),'<TD DAT>','exec'),globals_)
            globals_['_rebuild_router']()
            self.assertEqual(observed,[(str(builder),'__main__')])


if __name__=='__main__':unittest.main()
