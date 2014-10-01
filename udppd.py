#!/usr/bin/python
import multiprocessing
import ConfigParser
import os
from optparse import OptionParser
import subprocess
import json
import sys
import shutil
from pprint import pprint

class config_error(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)

class process_error(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)


class filedata:
    fileclass=None
    video_info=None
    filename=None
    exists=False   
     
    def __init__(self, f, opts):
        self.opts=opts
        self.setclass("Not Set", False)
        if opts==None:
            self.opts=dict()
            self.opts['video']=dict()
            self.opts['video']['vbitrate']=200000
            self.opts['video']['abitrate']=9600
            self.opts['video']['format']='mkv'
        self.setfilename(f)
       
        
        
    def setfilename(self,f):
        self.filename=f
        self.classify()
        self.generate_proposed_filename()
        if self.video == True:
            self.do_bitrate_stuff()
        
    def do_bitrate_stuff(self):
        max=int(self.opts['video']['vbitrate'])
        current=int(self.formatdata['bit_rate'])
        if current < max :
            self.target_vbitrate=str(current)
        else:
            print "max vbitrate %s currnet vbitrate %s : Limiting" % ( max, current)
            self.target_vbitrate=str(max)
        self.target_abitrate=str(self.opts['video']['abitrate'])
        
    def set_proposed_filename(self,f):
        self.proposed_filename=f
        
    def generate_proposed_filename(self, newext=None):
        if newext is None:
            newext=self.opts['video']['format']
        print "Generating New Filename for %s" % self.filename

        if self.filename.find('/') >= 0 :
            (dir,filename)=str(self.filename).rsplit('/',1)
        else:
            dir="."
            filename=self.filename
        if filename.find('.') > 0 :
            (filename, ext) =  filename.rsplit('.',1) 
            
            
        if ( newext is not None): 
            proposed=".".join((filename, newext))
        else:
            proposed=".".join((filename, ext))
#        if dir is not None :
#            proposed="/".join((dir, proposed))
        print("Proposing \"%s\"" % proposed)
        self.set_proposed_filename(proposed)

    def setclass(self,fc,v):
        self.fileclass=fc
        self.video=v
        print "Setting %s    fileclass:%s  video:%s" % (self.filename, self.fileclass, self.video)
        
    def classify(self):
        if os.path.isfile(self.filename):
            print " file %s exists" % self.filename
            self.exists = True
            self.probevideo()
            if self.video_info.has_key('format') :
                format_name=str(self.video_info['format']['format_name'])
                print format_name 
                if format_name == 'tty':
                    self.setclass("Text", False)
                elif format_name == 'matroska,webm':
                    self.setclass("Video", True)
                elif format_name == 'avi':
                    self.setclass("Video", True)
                elif format_name == 'mov,mp4,m4a,3gp,3g2,mj2':
                    self.setclass("Video", True)
                else :
                    self.setclass("Unknown", False)
            else:
                self.setclass('Unknown', False)
        else:
            print " file %s does NOT exists" % self.filename
            self.exists = False
            self.setclass("Non-Existent",False)
            
        if self.video is True:
            self.video_stream=self.select_video_stream()
            self.audio_stream=self.select_audio_stream()
            self.formatdata=self.video_info['format']
            
    def select_video_stream(self):
        for stream in self.video_info['streams']:
            if stream['codec_type'] == 'video':
                return(stream)
            
    def select_audio_stream(self):
        for stream in self.video_info['streams']:
            if stream['codec_type'] == 'audio':
                return(stream)
            
    def process(self, dest_dir, newheight=None, desttype="mkv"):

        pprint(self.formatdata['bit_rate'])
        
        if newheight is None:
            newheight=self.opts['video']['vsize']
        old_height=self.video_stream['height']
        old_width=self.video_stream['width']
        print "Old H: %i  W: %i" %(old_height, old_width)
        new_height = old_height
        new_width  = old_width
        if old_height > 720 :
            new_height=720
            new_width = old_width * ( float(new_height)/float(old_height))
            
        self.dest_size="%ix%i" %(new_width,new_height)

        print ("Config options:")
        pprint(self.opts['video'])

        cmd = ["ffmpeg",
             "-i", self.filename,
             "-v", "warning",
             "-s", self.dest_size,
             "-vcodec", "libx264",
             "-preset", self.opts['video']['preset'],
             "-preset", self.opts['video']['recodespeed'],
             "-vb", self.target_vbitrate,
             "-acodec", "ac3",
             "-ab", self.target_abitrate,
             "%s/%s" % (dest_dir, self.proposed_filename)
             ]
        print("Cmd: ",str(' ').join(cmd))
        print("Starting")
        ffmpeg=subprocess.Popen(cmd,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                close_fds=True)
        print("running")
        print(ffmpeg.stdout.read())
        print("Ending")
            
    def status(self):
        return("Not Implemented")


    def probevideo(self):
        ffmpeg=subprocess.Popen(["ffprobe", "-print_format", "json", "-show_format", "-show_streams",  "-v", "quiet", self.filename],
                                 stdout=subprocess.PIPE, close_fds=True)
        self.video_info=json.loads(ffmpeg.stdout.read())
        
         


class process_job:
    files=None
    def __init__(self, video_dir, opts=None):
        self.status="initializing"
        self.files=list()
        self.opts=opts
        self.video_dir = video_dir
        
        self.lock = multiprocessing.Lock()
        
        if os.access(video_dir, os.X_OK|os.W_OK|os.R_OK) :
            pass
        else:
            raise(config_error("Can't rwx %s" % video_dir))
        
        self.origdir="orig"
        while os.access("%s/%s" % (video_dir,self.origdir), os.X_OK|os.W_OK|os.R_OK):
            self.origdir="%s_" % self.origdir
#        self.origdir="%s/%s" % ( self.video_dir, self.origdir)
        
    def prep(self):
        self.status="scanning"
        os.mkdir("%s/%s"%(self.video_dir,self.origdir))
        for f in os.listdir(self.video_dir):
            if f == self.origdir :
                pass
            else:         
                
                print ("preping %s/%s" %( self.video_dir,f), "%s/%s" % (self.video_dir,self.origdir))
                shutil.move("%s/%s" %( self.video_dir,f), "%s/%s" % (self.video_dir,self.origdir))
        if self.origdir != "orig" :
            shutil.move("%s/%s" %( self.video_dir,self.origdir), "%s/%s" % (self.video_dir,'orig'))
        self.origdir="%s/%s" % (self.video_dir,'orig')
        self.destdir="%s/%s" % (self.video_dir,'dest')
        os.mkdir(self.destdir)
        
        print "Orig dir is %s, adding files to it: " %self.origdir
        for f in os.listdir(self.origdir):
            print "Adding %s" % f 
            self.files.append(filedata("%s/%s"%(self.origdir,f),self.opts))
        print "Listing self.files"
        for f in self.files:
            print f.filename, f.fileclass
        self.status="waiting"
            
    def get_status(self):
        return self.status
    
    def run(self):
        pprint(self.lock)
        if self.lock.acquire(timeout=0):
            child=multiprocessing.Process(target=self.run_foreground(),args=())
        else:
            raise( process_error("File already running"))


            
    def run_foreground(self, lock=None):
        self.status="Starting"
        for f in self.files:
            if f.fileclass == "Video":
                print "Process video file %s" % (f.filename)
                f.process(self.destdir)
            else:
                print "Processing non-video file %s" % (f.filename)
                if os.path.isfile(f.filename):
                    shutil.copy2(f.filename, self.destdir)
                elif os.path.isdir(f.filename):
                    subjob=process_job(f.filename, self.opts)
                    subjob.run_foreground()
                    shutil.move(f.filename,self.destdir)
        self.status="OK"
        if lock is not None:
            lock.release()
            
        
    def clean_old(self):
        shutil.rmtree(self.origdir)
        for f in os.listdir(self.destdir):
            shutil.move("%s/%s"%(self.destdir,f), self.video_dir)
            print("Cleaning %s" % (f))

class main:
    opts=None
    args=None
    def __init__(self, configfilename=None, runtests=False, opts=None):
        self.opts=dict()
        self.args=dict()
        self.opts['processdir']=None
        self.opts['daemon']=False
        self.opts['configfilename']=configfilename
        self.opts['runtests']=runtests

        if opts is not None:
            for (k,v ) in opts:
                self.opts[k]=v
            
    
        if self.opts['runtests'] is True:
                self.tests()
        else:
            self.parse_args()
        
        self.load_config()
        self.verify_config()
        
        if self.opts["processdir"] is not None:
            job=process_job(self.opts["processdir"], self.opts)
            job.prep()
            job.run_foreground(None)
            job.clean_old()
        elif self.opts["daemon"] is True:
            raise(config_error("Not implemented"))
        else :
            pass
            
                
    def parse_args(self):
        param_parser = OptionParser()
        param_parser.add_option("-c", "--config",  dest="configfilename",   default="/etc/udppd.conf", help="config file",          metavar="FILE")
        param_parser.add_option("-p", "--process", dest="processdir",       default=None            , help="directory to process", metavar="FILE")
        param_parser.add_option("-D", "--Daemon", dest="daemon",       default=False            , help="Run as service" )
        (opts, args) = param_parser.parse_args()
        
        self.opts['processdir']=opts.processdir
        self.opts['daemon']=opts.daemon
        self.opts['configfilename']=opts.configfilename
        self.opts['opts']=opts
        self.opts['args']=args
        self.opts['runtests']=False

    def load_config(self):
        if not os.path.isfile(self.opts['configfilename']):
            raise(config_error("Configuration File not found: %s" % self.opts['configfilename']))
                          
            

        config = ConfigParser.ConfigParser()
        config.read(self.opts['configfilename'])
        for section in config.sections():           
            self.opts[section]=dict()
            for (k,v) in config.items(section):
                self.opts[section][k]=v
        
                        

    def verify_config(self):
        for k in ('udppd','video'):
            if self.opts.has_key(k):
                pass
            else:
                raise(config_error("Missing config file section: %s" % k))        


    def tests(self):
        print "Running tests"

    def run(self):
        running=True;
        exit_value=0

        if self.opts['runtests'] is True:
                running=False

        while running:
            running=False
        sys.exit(exit_value)

if __name__ == "__main__":
    main=main()
    #main.run()
        
