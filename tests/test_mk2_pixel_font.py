"""Pixel-font and LCD legibility acceptance; checks pixels and drawn bounds."""
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from pixelblaze_mapper.mk2_pixel_font import PixelFont
from pixelblaze_mapper.maschine_mk2 import render


def mask_image(font, text):
    mask = font.getmask(text)
    image = Image.new('1', mask.size)
    image.putdata(list(mask))
    return image


def snapshot():
    parameters = [dict(id=str(i),name='Parameter '+str(i),abbreviation='Speed' if i==0 else 'Par'+str(i),
                       value=.125,min=0,max=1,editable=True) for i in range(8)]
    cards = [dict(label='Öl Material '+str(i+1),image=None,number=i+1,available=True,kind='material')
             for i in range(16)]
    c = dict(mode='material',screen='home',material=dict(id='active',label='Öl Äther Überblendung',image=None),
             parameter_pages=[dict(label='TD',parameters=parameters)],page=0,bank=0,pad_index=0,
             cards=cards,focused_parameter=None,recording=False,parameter_overflow=0,
             browse_items=[dict(id=str(i),label='Größe Äther Material '+str(i),category='Wärme',
                               assignments=[dict(group=0,pad=i%16)]) for i in range(20)],
             browse_index=2,options=['Select','Edit','Browse','Delete'],choice=0,confirm=None,error='',
             show=dict(playing=True,state='playing',elapsed=5.,duration=20.,progress=.25,
                       transition='crossfade',transition_duration=2.,transition_progress=.5,
                       focus='duration',editing=False))
    return dict(controller=c,cards=cards,selected=0,images={},version=1)


class PixelGlyphTests(unittest.TestCase):
    def test_empty_text_masks_work_at_both_integer_scales(self):
        for scale in (1,2):
            font=PixelFont(scale)
            with self.subTest(scale=scale):
                self.assertEqual(font.getlength(''),0)
                self.assertEqual(font.getmask('').size,(0,7*scale))

    def test_accent_fallback_and_unknown_unicode_stay_visible(self):
        font=PixelFont()
        self.assertEqual(tuple(font.getmask('é')),tuple(font.getmask('e')))
        self.assertEqual(tuple(font.getmask('素材')),tuple(font.getmask('??')))
        self.assertIsNotNone(mask_image(font,'素材').getbbox())

    def test_masks_are_native_one_bit_and_numeric_glyphs_are_distinct(self):
        font = PixelFont()
        digits = []
        for glyph in '0123456789':
            mask = font.getmask(glyph)
            self.assertEqual(mask.mode,'1')
            self.assertEqual(mask.size[1],7)
            self.assertLessEqual(len(set(mask)),2)
            self.assertGreater(max(mask),0)
            digits.append(tuple(mask))
        self.assertEqual(len(set(digits)),10)

    def test_umlats_and_sharp_s_have_visible_distinct_shapes(self):
        font = PixelFont()
        for accented,plain in (('Ä','A'),('Ö','O'),('Ü','U'),('ä','a'),('ö','o'),('ü','u')):
            with self.subTest(glyph=accented):
                self.assertNotEqual(tuple(font.getmask(accented)),tuple(font.getmask(plain)))
                self.assertIsNotNone(mask_image(font,accented).getbbox())
        self.assertNotEqual(tuple(font.getmask('ß')),tuple(font.getmask('?')))

    def test_fixed_advance_leaves_a_full_blank_column_between_glyphs(self):
        font=PixelFont()
        self.assertEqual(font.getlength('Speed 1.25'),59)
        self.assertEqual(font.getlength('AA')-font.getlength('A'),6)
        image=mask_image(font,'MW8')
        for x in (5,11):
            self.assertFalse(any(image.getpixel((x,y)) for y in range(7)))
        self.assertEqual(font.getlength(''),0)

    def test_large_font_is_exact_integer_pixel_expansion(self):
        normal=mask_image(PixelFont(scale=1),'Ä 012.5')
        large=mask_image(PixelFont(scale=2),'Ä 012.5')
        self.assertEqual(large.size,(normal.width*2,normal.height*2))
        self.assertEqual(large.tobytes(),normal.resize(large.size,Image.Resampling.NEAREST).tobytes())
        self.assertEqual(PixelFont(scale=2).getlength('123'),34)


class DisplayLegibilityTests(unittest.TestCase):
    def draw_with_text_positions(self,s):
        records=[]
        original=ImageDraw.ImageDraw.text
        def capture(draw,xy,text,*args,**kwargs):
            font=kwargs.get('font')
            if text:
                records.append((tuple(xy),str(text),font,font.getbbox(str(text))))
            return original(draw,xy,text,*args,**kwargs)
        with patch.object(ImageDraw.ImageDraw,'text',capture):
            frames=render(s)
        return frames,records

    def test_all_view_text_uses_pixel_font_and_fits_inside_each_lcd(self):
        for mode in ('material','show'):
            for screen in ('home','browse','pad_grid','pad_menu','pad_edit',
                           'confirm_assign','confirm_delete','confirm_edit'):
                s=snapshot();c=s['controller'];c.update(mode=mode,screen=screen)
                c['material']['label']='Sehr langer Materialname ÄÖÜ '+('W'*80)
                if screen.startswith('confirm_'):
                    c['confirm']=dict(label='Löschen oder Änderungen speichern?',options=['Confirm','Cancel'],choice=0)
                with self.subTest(mode=mode,screen=screen):
                    frames,records=self.draw_with_text_positions(s)
                    self.assertTrue(records)
                    self.assertEqual([(f.mode,f.size) for f in frames],[('1',(256,64))]*2)
                    for (x,y),text,font,(left,top,right,bottom) in records:
                        self.assertIsInstance(font,PixelFont,msg=text)
                        self.assertGreaterEqual(x+left,0,msg=text)
                        self.assertGreaterEqual(y+top,0,msg=text)
                        self.assertLessEqual(x+right,256,msg=text)
                        self.assertLessEqual(y+bottom,64,msg=text)

    def test_parameter_text_has_blank_row_before_bar_and_separate_columns(self):
        right=render(snapshot())[1]
        for row in range(4):
            # Seven native rows at 12 + row*13; one blank row before its bar.
            y=12+row*13
            for start in (3,131):
                self.assertTrue(any(right.getpixel((x,yy)) for x in range(start,start+121) for yy in range(y,y+7)))
                self.assertFalse(any(right.getpixel((x,y+7)) for x in range(start,start+121)))
                self.assertTrue(all(right.getpixel((x,y+8)) for x in range(start,start+121)))
        self.assertFalse(any(right.getpixel((x,y)) for x in range(124,131) for y in range(11,64)))
        self.assertFalse(any(right.getpixel((x,63)) for x in range(256)))

    def test_selected_browse_row_does_not_touch_next_row(self):
        s=snapshot();c=s['controller'];c.update(screen='browse',browse_index=2)
        left=render(s)[0]
        selected_top=22+2*10
        # Highlight occupies nine rows including padding, leaving the tenth clear.
        self.assertFalse(any(left.getpixel((x,selected_top+9)) for x in range(2,253)))
        self.assertTrue(any(left.getpixel((x,selected_top+10)) for x in range(2,253)))

    def test_pad_names_stay_inside_boxes_and_leave_separator_rows_empty(self):
        s=snapshot();s['controller']['screen']='pad_grid'
        frames=render(s)
        for frame in frames:
            for y in (15,31,47,63):
                self.assertFalse(any(frame.getpixel((x,y)) for x in range(256)))
            for y in range(64):
                self.assertEqual(frame.getpixel((127,y)),0)

    def test_top_tabs_fit_their_own_button_cell_without_touching_border(self):
        s=snapshot();c=s['controller']
        c['parameter_pages']=[dict(label='TD' if i==0 else 'MM '+str(i),parameters=[]) for i in range(8)]
        c['parameter_overflow']=192;c['page']=7
        _,records=self.draw_with_text_positions(s)
        tabs=[record for record in records if record[0][1]==1]
        self.assertEqual(len(tabs),8)
        for (x,y),text,font,(_,_,right,bottom) in tabs:
            cell=(x//64)*64
            self.assertGreater(x,cell)
            self.assertLessEqual(x+right,cell+62,msg=text)
            self.assertLessEqual(y+bottom,9,msg=text)

    def test_error_footer_and_large_focused_value_have_unclipped_pixel_bounds(self):
        s=snapshot();c=s['controller'];c['mode']='show'
        c['focused_parameter']=dict(name='Überblendung Intensität',value=-123.456,min=-200,max=200)
        c['error']='Änderung nicht verfügbar: '+('X'*70)
        _,records=self.draw_with_text_positions(s)
        error=[r for r in records if r[0][1]==54]
        self.assertEqual(len(error),1)
        self.assertLessEqual(error[0][0][1]+error[0][3][3],64)
        value=next(r for r in records if r[1]=='-123.456')
        self.assertEqual(value[3][3]-value[3][1],14)
        self.assertLessEqual(value[0][1]+value[3][3],48)

    def test_error_footer_replaces_intersecting_rows_completely_and_keeps_right_display(self):
        expected=Image.new('1',(256,11))
        ImageDraw.Draw(expected).text((2,1),'Fehlerhinweis',font=PixelFont(),fill=1)
        for screen in ('home','browse','pad_grid','pad_menu','pad_edit','confirm_assign'):
            s=snapshot();c=s['controller'];c['screen']=screen
            if screen=='confirm_assign':
                c['confirm']=dict(label='Zuweisung',options=['Confirm','Cancel'],choice=0)
            before=render(s)
            c['error']='Fehlerhinweis'
            with self.subTest(screen=screen):
                frames,records=self.draw_with_text_positions(s)
                self.assertEqual(before[1].tobytes(),frames[1].tobytes())
                self.assertEqual(frames[0].crop((0,53,256,64)).tobytes(),expected.tobytes())
                texts=[record[1] for record in records]
                if screen in ('pad_menu','confirm_assign'):
                    self.assertNotIn('Drehen: waehlen / Druecken: OK',texts)
                if screen=='browse':
                    self.assertFalse(any(text.startswith('004 ') for text in texts))

    def test_favorites_browser_tabs_align_with_physical_buttons_and_all_text_fits(self):
        for favorites, empty, assign in ((False,False,False),(True,False,False),(True,True,False),(True,True,True)):
            s=snapshot();c=s['controller']
            c.update(screen='browse',browse_filter='favorites' if favorites else 'all',favorites_count=0 if empty else 20,
                     browse_purpose='assign' if assign else 'load',bank=1,pad_index=5)
            for item in c['browse_items']:
                item.update(favorite=True,label='Sehr langer Favoritenname '+('X'*80))
            if empty:c['browse_items']=[]
            with self.subTest(favorites=favorites,empty=empty,assign=assign):
                _,records=self.draw_with_text_positions(s)
                tabs=[r for r in records if r[0][1]==1]
                self.assertEqual([(r[0][0],r[1]) for r in tabs],[(3,'ALLE'),(67,'FAV'),(195,'+FAV' if empty else '-FAV')])
                for (x,y),text,font,(_,_,right,bottom) in records:
                    self.assertLessEqual(x+right,256,msg=text)
                    self.assertLessEqual(y+bottom,64,msg=text)
                texts=[r[1] for r in records]
                if empty:
                    self.assertIn('Noch keine Favoriten',texts)
                    self.assertIn('Mit +FAV markieren',texts)
                if assign:self.assertIn('PAD B06 ZUORDNEN',texts)

    def test_long_name_clipping_is_visible_and_missing_image_caption_is_complete(self):
        s=snapshot();s['controller']['material']['label']='Material '+('X'*90)
        _,records=self.draw_with_text_positions(s)
        texts=[record[1] for record in records]
        name=next(text for text in texts if text.startswith('Material X'))
        self.assertTrue(name.endswith('…'))
        self.assertIn('Kein',texts)
        self.assertIn('Bild',texts)


if __name__=='__main__':
    unittest.main()
