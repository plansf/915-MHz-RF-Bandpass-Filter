import json
from pathlib import Path
import tempfile
import unittest
from argparse import Namespace
import numpy as np
import rf915 as r

CFG=json.loads((r.ROOT/'design.json').read_text())

class PhysicsTests(unittest.TestCase):
    def test_matched_through_line(self):
        f=np.linspace(1e6,2e9,100)
        s=r.abcd_to_s(r.line(f,20,loss_db_per_m=0))
        np.testing.assert_allclose(s[:,0,0],0,atol=1e-14)
        np.testing.assert_allclose(abs(s[:,1,0]),1,atol=1e-14)
        gd=-np.gradient(np.unwrap(np.angle(s[:,1,0])),2*np.pi*f)
        np.testing.assert_allclose(gd,.02*np.sqrt(3.1)/299792458,rtol=1e-10)

    def test_ideal_against_independent_nodal_solution(self):
        # Solve two-node reduced circuit directly, independent of ABCD implementation.
        for f in [433e6,915e6,1830e6]:
            w=2*np.pi*f;c=CFG['components']
            zl=1/(1j*w*c['C1']*1e-12)+1j*w*c['L1']*1e-9
            zr=1/(1j*w*c['C3']*1e-12)+1j*w*c['L3']*1e-9
            yp=1/(1j*w*c['L2']*1e-9)+1j*w*c['C2']*1e-12
            # Source voltage 1V with 50R; output loaded by 50R.
            yc=1/(50+zl)
            a=np.array([[yc+yp+1/zr,-1/zr],[-1/zr,1/zr+1/50]],complex)
            vm,vo=np.linalg.solve(a,np.array([yc,0]))
            iin=(1-vm)/(50+zl);vin=1-50*iin
            s=r.simulate(np.array([f]),CFG,ideal=True)[0]
            self.assertAlmostEqual(abs(s[1,0]-2*vo),0,places=12)
            self.assertAlmostEqual(abs(s[0,0]-(2*vin-1)),0,places=12)

    def test_reciprocity_and_passivity(self):
        f=np.linspace(200e6,2200e6,4001)
        for ideal in [True,False]:
            s=r.simulate(f,CFG,ideal)
            np.testing.assert_allclose(s[:,0,1],s[:,1,0],atol=1e-12)
            self.assertLessEqual(np.linalg.svd(s,compute_uv=False).max(),1+1e-10)

    def test_vendor_model_low_frequency(self):
        z=r.inductor(np.array([1e6]),15)[0]
        self.assertGreater(z.real,.078)
        self.assertAlmostEqual(z.imag/(2*np.pi*1e6),15e-9,delta=.01e-9)

class TouchstoneTests(unittest.TestCase):
    def test_simulation_cannot_be_labeled_measured(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);p=folder/'input.s2p';meta=folder/'meta.json'
            f=np.linspace(850e6,1000e6,301)
            r.write_s2p(p,f,r.simulate(f,CFG),'SIMULATED fixture')
            meta.write_text(json.dumps({key:'test' for key in ('instrument','date','calibration','reference_plane','board_revision','operator')}))
            args=Namespace(input=p,output=folder/'out',kind='measured',metadata=meta,reference=None)
            with self.assertRaisesRegex(ValueError,'SIMULATED'):
                r.analyze(args,CFG)

    def test_roundtrip_and_pair_order(self):
        f=np.array([902e6,915e6,928e6])
        s=np.array([[[.1+.2j,.3+.4j],[.5+.6j,.7+.8j]]]*3)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.s2p';r.write_s2p(p,f,s,'SIMULATED test fixture')
            ff,ss=r.read_s2p(p)
            np.testing.assert_allclose(ff,f);np.testing.assert_allclose(ss,s)

    def test_db_and_ma_with_wrapped_rows(self):
        for encoding,one in [('DB','-6.020599913 90'),('MA','.5 90')]:
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'a.s2p'
                p.write_text(f'# MHz S {encoding} R 50\n902 {one} 1 0 ! comment\n0 0 0 0\n928 {one} 1 0 0 0 0 0\n')
                f,s=r.read_s2p(p)
                np.testing.assert_allclose(f,[902e6,928e6]);np.testing.assert_allclose(s[:,0,0],.5j,atol=1e-10)

    def test_reject_bad_reference_and_axis(self):
        for text in ['# Hz S RI R 75\n1 0 0 1 0 1 0 0 0\n2 0 0 1 0 1 0 0 0',
                     '# Hz S RI R 50\n2 0 0 1 0 1 0 0 0\n1 0 0 1 0 1 0 0 0',
                     '[Version] 2.0\n']:
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'a.s2p';p.write_text(text)
                with self.assertRaises(ValueError):r.read_s2p(p)

    def test_missing_stopband_is_unknown(self):
        f=np.linspace(850e6,1000e6,301)
        m=r.metrics(f,r.simulate(f,CFG),CFG)
        self.assertTrue(m['passband_pass'])
        self.assertIsNone(m['overall_pass'])
        self.assertIsNone(m['stopband']['1830']['pass'])

    def test_reject_sparse_passband(self):
        f=np.array([200e6,915e6,2200e6])
        with self.assertRaises(ValueError):r.metrics(f,r.simulate(f,CFG),CFG)

if __name__=='__main__':unittest.main()
