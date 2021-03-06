'''
sun grid engine util functions
'''


import sys,os,datetime,time

def get_vmem_rt(jobnumber,rec):
    '''
    look for a file containing the job script
    try to extract h_vmem and h_rt
    '''
    
    rec['h_vmem'] = '-'
    rec['h_rt'] = '-'
    
    fname = qsub_log_dir+'/'+jobnumber+'.sge'
    if not os.path.isfile(fname): return
    
    f = open(fname)
    read = f.read().split('\n')
    f.close()
    
    try:
        h_vmem = [x.strip() for x in read if x.startswith('#$ -l h_vmem=')]
        h_rt = [x.strip() for x in read if x.startswith('#$ -l h_rt=')]
        rec['h_vmem'] = h_vmem[0].split('=')[1]
        rec['h_rt'] = h_rt[0].split('=')[1]
    except:
        pass

def seconds_to_hhmmss(ss):
    mm, ss = divmod(ss, 60)
    hh, mm = divmod(mm, 60)
    return "%d:%02d:%02d"%(hh,mm,ss)

def get_qacct_info(user):
    data = subprocess.check_output('qacct -o '+user+' -j',shell=True)

    #chop off summary stats
    data = data[:-3]
    assert data[-1].startswith('arid')

    data = '\n'.join(data).split('==============================================================')
    data = [x for x in data if x!= '']
    data = [x.strip().split('\n') for x in data]

    for i,rec in enumerate(data):
        dic = {}
        for x in rec:
            x = x.strip().split()
            key = x[0]
            val = ' '.join(x[1:])
            dic[key] = val
            
        fields = ['jobname','jobnumber','failed','exit_status','maxvmem','qsub_time','start_time','end_time','ru_wallclock','hostname']
        data[i] = {k:dic[k] for k in fields}
        data[i]['ru_wallclock'] = seconds_to_hhmmss(int(data[i]['ru_wallclock']))
        data[i]['h_vmem'] = '-'
        data[i]['h_rt'] = '-'
        data[i]['failed'] = data[i]['failed'].strip().split()[0]
        
        get_vmem_rt(data[i]['jobnumber'],data[i])
        
    return data
    
def parse_american_date(inp):
    '''
    mm/dd/yyyy hh:mm:ss -> datetime object
    '''

    datestr = inp.strip().split()[0]
    year = int(datestr.split('/')[2])
    month = int(datestr.split('/')[0])
    day = int(datestr.split('/')[1])
    
    timestr = inp.strip().split()[1]
    hour = int(timestr.split(':')[0])
    minute = int(timestr.split(':')[1])
    second = int(timestr.split(':')[2])
    
    return datetime.datetime(year, month, day, hour, minute, second)

def get_qstat_info(user):
    data = subprocess.check_output('qstat -u '+user,shell=True)

    if len(data) < 3: exit()

    data = data[2:]

    item_list = []

    for job in data:
        jobid = job.strip().split()[0]
        state = job.strip().split()[4].strip()
        stime = job.strip().split()[5] + ' ' + job.strip().split()[6] #sub / start time
        rec = subprocess.check_output('qstat -j '+str(jobid),shell=True)
        
        fields = ['jobname','jobnumber','failed','exit_status','h_vmem','maxvmem','h_rt','ru_wallclock']
        item = {k:'-' for k in fields}
        
        item['jobnumber'] = jobid
        item['jobname'] = [x.strip() for x in rec if x.startswith('job_name:')][0].split()[1].strip()
        
        if state == 'r':
            #get maxvmem from qstat info
            maxvmem = [x.strip() for x in rec if x.startswith('usage    1:')][0]
            maxvmem = [x for x in maxvmem.split() if x.startswith('maxvmem')][0]
            item['maxvmem'] = maxvmem.split('=')[1].strip().strip(',')

            #calculate running time from current time and start time
            delta = datetime.datetime.now() - parse_american_date(stime)
            item['ru_wallclock'] = seconds_to_hhmmss(int(delta.total_seconds()))
            item['exit_status'] = 'RUN'
            
        elif state == 'qw':
            item['exit_status'] = 'QUEUED'
        
        elif state == 't':
            item['exit_status'] = 'START'
            
        elif 'E' in state:
            item['exit_status'] = 'ERROR'
            
        else:
            item['exit_status'] = '????'
            
        get_vmem_rt(jobid,item)
        
        item_list.append(item)
        
    return item_list
