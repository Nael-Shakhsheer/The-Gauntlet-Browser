"""Read-only PNG/metadata validation for the integrated visual pass."""
import json
from pathlib import Path
import unittest
from PIL import Image,ImageChops,ImageStat

ROOT=Path(__file__).resolve().parents[1]

class VisualAssetTests(unittest.TestCase):
    def test_all_forms_binary_alpha_safe_cells_and_mirrors(self):
        for hero in ('knight','wizard','archer','cleric','rogue','druid','bard','healer'):
            meta=json.loads((ROOT/f'static/sprites/ascended-{hero}-v1.json').read_text(encoding='utf-8-sig'))
            self.assertEqual(meta['anchor'],[48,84]);self.assertEqual(len(meta['directions']),8)
            for kind,columns in [('body',8),('actions',9)]:
                with Image.open(ROOT/'static/sprites'/meta['sheets'][kind]) as img:
                    self.assertEqual(img.size,(columns*96,768));self.assertEqual(img.mode,'RGBA')
                    self.assertLessEqual(set(img.getchannel('A').getdata()),{0,255})
                    for row in range(8):
                        for col in range(columns):
                            cell=img.crop((col*96,row*96,(col+1)*96,(row+1)*96));bbox=cell.getchannel('A').getbbox()
                            self.assertIsNotNone(bbox);self.assertGreaterEqual(bbox[0],2);self.assertGreaterEqual(bbox[1],2);self.assertLessEqual(bbox[2],94);self.assertLessEqual(bbox[3],84)
                    for dest,source in [(5,3),(6,2),(7,1)]:
                        a=img.crop((0,dest*96,columns*96,(dest+1)*96))
                        for col in range(columns):
                            expected=img.crop((col*96,source*96,(col+1)*96,(source+1)*96)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                            actual=a.crop((col*96,0,(col+1)*96,96));self.assertIsNone(ImageChops.difference(actual,expected).getbbox())

    def test_region_transparency_and_size(self):
        for filename,columns,rows in [('region-props-v1.png',4,4),('travel-shrines-v2.png',2,3)]:
            with Image.open(ROOT/'static/sprites'/filename) as image:
                self.assertEqual(image.size,(columns*160,rows*160));self.assertLessEqual(set(image.getchannel('A').getdata()),{0,255})
                for row in range(rows):
                    for col in range(columns):
                        b=image.crop((col*160,row*160,(col+1)*160,(row+1)*160)).getchannel('A').getbbox();self.assertIsNotNone(b);self.assertGreater(b[0],10);self.assertGreater(b[1],5);self.assertLessEqual(b[3],144)
        with Image.open(ROOT/'static/sprites/dungeon-map-cellar-v1.png') as image:self.assertEqual(image.size,(960,540))
