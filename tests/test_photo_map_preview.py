import unittest
import numpy as np
from pixelblaze_mapper.photo_map_preview import homography, project

UNIT=((0,1),(1,1),(0,0),(1,0))

class PhotoMapTests(unittest.TestCase):
    def test_homography_corners(self):
        quad=((.1,.9),(.8,.7),(.2,.1),(.9,.2))
        np.testing.assert_allclose(homography(np.array(UNIT),quad),quad)

    def points(self):
        p=np.zeros((3744,3))
        for a,b in ((0,517),(517,786),(786,1184)):
            p[a:b,0]=np.linspace(0,1,b-a);p[a:b,1]=np.linspace(1,0,b-a)
        p[1184:,0]=.9;p[1184:,2]=.6
        return p

    def test_scanned_left_uses_photo_left_not_source_block(self):
        p=self.points(); p[1184]=(.9,1,.4); p[1440]=(.9,1,.6)
        quads=[UNIT for _ in range(10)]
        quads[1]=((2,1),(3,1),(2,0),(3,0))
        xy,v=project(p,quads,{k:UNIT for k in ('Upper','Middle','Lower')},[(1643,1695)])
        np.testing.assert_allclose(xy[1184],(2.5,.5))
        np.testing.assert_allclose(xy[1440],(.5,.5))
        self.assertEqual(int(v.sum()),3691)
        self.assertFalse(v[1643]);self.assertTrue(v[1642]);self.assertTrue(v[1696])

    def test_true_scan_shape_and_color_indices_preserved(self):
        p=self.points();p[1440]=(.984375,1,.684375);p[1441]=(.9,1,.6)
        xy,v=project(p,[UNIT]*10,{k:UNIT for k in ('Upper','Middle','Lower')})
        np.testing.assert_allclose(xy[1440],(0,1),atol=1e-12)
        np.testing.assert_allclose(xy[1441],(.5,.5))
        self.assertEqual(len(xy),3744)

    def test_side_face_orientation(self):
        xy,_=project(self.points(),[UNIT]*10,{k:UNIT for k in ('Upper','Middle','Lower')})
        np.testing.assert_allclose(xy[517],(0,0),atol=1e-12)
        np.testing.assert_allclose(xy[785],(1,1))

    def test_degenerate_calibration_rejected(self):
        with self.assertRaises(np.linalg.LinAlgError):homography(np.array([[.5,.5]]),[(0,0)]*4)

if __name__=='__main__':unittest.main()
