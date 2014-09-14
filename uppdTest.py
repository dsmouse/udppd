import unittest
from uppd import *
from pprint import pprint
import shutil
import errno


class mainTest(unittest.TestCase):
    def setUp(self):
        self.main=main(runtests=True, configfilename="./testdata/testconfig.conf")
        
    def tearDown(self):
        pass
    
    def test_main_config(self):
        pass
    
    
class fileTest(unittest.TestCase):
    def setUp(self):
        self.configfilename="./testdata/testconfig.conf"
        shutil.rmtree("./filetestss", ignore_errors=True)
        try:
            os.mkdir("./filetestss/")
        except:
            pass
    
        shutil.copytree("./testdata", "./filetestss/test-a")
        
        self.main=main(runtests=True, configfilename=self.configfilename)
        
    def tearDown(self):
        pass
    
    def test_main_config(self):
        pass
    
    def test_no_opts(self):
        x=filedata("test.ext", None)
        
    def test_new_no_file(self):
        x=filedata("test.ext", main.opts)
        x=filedata("./filetess/test.ext", main.opts)
        
    
    def test_file_avi2mkv(self):
        x=filedata("./filetestss/test-a/Karate-WhiteS01E2.avi", None) 
        pprint (x)
        print x.proposed_filename.endswith("mkv")
        assert x.proposed_filename.endswith("mkv")

class cmdlTest(unittest.TestCase):
    def setUp(self):
        
        self.configfilename="./testdata/testconfig.conf"
        shutil.rmtree("./cmdltests", ignore_errors=True)
        try:
            os.mkdir("./cmdltests/")
        except:
            pass
    
        shutil.copytree("./testdata", "./cmdltests/test-a")
        
    def tearDown(self):
        pass
        
    def test_process(self):
        print os.getcwd()
        xfile=filedata("./cmdltests/test-a/Karate-WhiteS01E2.avi",None)
        assert xfile.exists is True
        opts=list()
        opts.append(['processdir',"./cmdltests/test-a"])
        xmain=subprocess.Popen(['/usr/bin/python','./uppd.py','-c','./testdata/testconfig.conf','-p','./cmdltests/test-a'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print xmain.stdout.read()
        xfile=filedata("./cmdltests/test-a/Karate-WhiteS01E2.avi",None)
        assert xfile.exists is False
        xfile=filedata("./cmdltests/test-a/Karate-WhiteS01E2.mkv",None)
        assert xfile.exists is True
        


class videoTest(unittest.TestCase):
    def setUp(self):
        
        self.main=main(runtests=True, configfilename="./testdata/testconfig.conf")
        self.main.opts        
        shutil.rmtree("./tests", ignore_errors=True)
        try:
            os.mkdir("./tests/")
        except:
            pass
    
        shutil.copytree("./testdata", "./tests/testa")
        shutil.copytree("./testdata", "./tests/testb")
        shutil.copytree("./testdata", "./tests/testc")
        shutil.copytree("./testdata", "./tests/testd")
        
    def tearDown(self):
        pass
        
    def test_baddir(self):
        try:
            job=process_job("./tests/no_dir",self.main.opts)
        except config_error as e:
            pprint(e)
        else:
            assert "No error found" == 1
        
    
    def test_background_job(self):
        bgjob=process_job("./tests/testb",self.main.opts)
        bgjob.prep()
        bgjob.run()
        try:
            bgjob.run()
        except process_error as e:
            pprint(e)
        else:
            assert "Ran twice fine"
            
        print bgjob.get_status()
        print "Status:",bgjob.get_status()
        assert bgjob.get_status() in ( "running", "OK" )
        
    def test_bgjob_works(self):
        bgjob=process_job("./tests/testc",self.main.opts)
        bgjob.prep()
        bgjob.run()
        i=60
        while bgjob is None:
            i=i-1
            assert i != 0 
        
        i=60
        while bgjob.get_status() == "running":
            i=i-1
            assert i > 0
                
        assert bgjob.get_status() == "OK"                  
        bgjob.clean_old()
        
    
    def test_dir(self):
        job=process_job("./tests/testa",self.main.opts)
        job.prep()
        job.run_foreground()
        assert job.get_status() == "OK"      
        job.clean_old()
        
    def test_detect_mkv(self):
        f=filedata('./testdata/TYR-Ormurin_Langi-360p.480p.mkv', self.main.opts)
        print "Type:",f.fileclass
        pprint(f.video_info)
        assert f.fileclass == 'Video'
        
    def test_detect_avi(self):
        f=filedata('./testdata/Karate-WhiteS01E2.avi', self.main.opts)
        print "Type:",f.fileclass
        pprint(f.video_info)
        assert f.fileclass == 'Video'
        
    def test_detect_text(self):
        f=filedata('./testdata/test.txt', self.main.opts)
        pprint(f.video_info)
        assert f.fileclass == 'Text'
        
    
    
    
    