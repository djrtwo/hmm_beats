"""
utils to process userstudies
"""

from UserStudy import UserStudy

def show_intel_use(studies, class_fun, descrip):
    ALL = 0
    NON = 1
    CLASS = 2
    intel_learn = [0, 0, 0]
    use_learn = [0, 0, 0]

    print 'ANALYSIS OF HOW MANY %s USERS PREFER THE HMM SYSTEM' % descrip
    print

    print "USER:\t%s\tINTEL\tUSE" % descrip
    for study in studies:
        print 'user%s:\t%s\t\t%s\t%s' % (study.id, class_fun(study), study.gen.intelligent, study.gen.use)

        if study.gen.intelligent == UserStudy.LEARN:
            intel_learn[ALL] = intel_learn[ALL] + 1
            if class_fun(study):
                intel_learn[CLASS] = intel_learn[CLASS] + 1
            else:
                intel_learn[NON] = intel_learn[NON] + 1

        if study.gen.use == UserStudy.LEARN:
            use_learn[ALL] = use_learn[ALL] + 1
            if class_fun(study):
                use_learn[CLASS] = use_learn[CLASS] + 1
            else:
                use_learn[NON] = use_learn[NON] + 1

    print

    num_users = float(len(studies))
    num_class = float(sum([class_fun(study) for study in studies]))
    num_nons = num_users - num_class

    intel_users = intel_learn[ALL] / num_users
    intel_nons = intel_learn[NON] / num_nons
    intel_class = intel_learn[CLASS] / num_class
    
    use_users = use_learn[ALL] / num_users
    use_nons = use_learn[NON] / num_nons
    use_class = use_learn[CLASS] / num_class

    print 'TOTAL USERS:\t%d' % num_users
    print 'TOTAL %s:\t%d' % (descrip, num_class)
    print
    print '\t\tALL\t\tNON\t\t%s' % descrip
    print 'INTEL_LEARN:\t%f\t%f\t%f' % (intel_users, intel_nons, intel_class)
    print 'USE_LEARN:\t%f\t%f\t%f' % (use_users, use_nons, use_class)

def show_averages(studies):

    l_coherence = [0] * 3
    l_musical = [0] * 3
    l_interesting = [0] * 3
    l_complexity = [0] * 3
    l_structured = [0] * 3
    l_surprising = [0] * 3
    l_satisfying = [0] * 3

    r_coherence = [0] * 3
    r_musical = [0] * 3
    r_interesting = [0] * 3
    r_complexity = [0] * 3
    r_structured = [0] * 3
    r_surprising = [0] * 3
    r_satisfying = [0] * 3
    
    for study in studies:
        for i, section in enumerate(study.sections):
            l_coherence[i] = l_coherence[i] + section.learn['coherence']
            l_musical[i] = l_musical[i] + section.learn['musical']
            l_interesting[i] = l_interesting[i] + section.learn['interesting']
            l_complexity[i] = l_complexity[i] + section.learn['complexity']
            l_structured[i] = l_structured[i] + section.learn['structured']
            l_surprising[i] = l_surprising[i] + section.learn['surprising']
            l_satisfying[i] = l_satisfying[i] + section.learn['satisfying']

            r_coherence[i] = r_coherence[i] + section.random['coherence']
            r_musical[i] = r_musical[i] + section.random['musical']
            r_interesting[i] = r_interesting[i] + section.random['interesting']
            r_complexity[i] = r_complexity[i] + section.random['complexity']
            r_structured[i] = r_structured[i] + section.random['structured']
            r_surprising[i] = r_surprising[i] + section.random['surprising']
            r_satisfying[i] = r_satisfying[i] + section.random['satisfying']


    num_studies = float(len(studies))
    for i in range(3):
        section = i+1
        print 'SECTION %s' % section
        print 'FEATURE\t\tRAND_AVG\tLEARN_AVG'
        l_coh = l_coherence[i] / num_studies
        r_coh = r_coherence[i] / num_studies
        print 'COH\t\t%f\t%f' % (r_coh, l_coh)
        l_mus = l_musical[i] / num_studies
        r_mus = r_musical[i] / num_studies
        print 'MUSICAL\t\t%f\t%f' % (r_mus, l_mus)
        l_int = l_interesting[i] / num_studies
        r_int = r_interesting[i] / num_studies
        print 'INTERESTING\t%f\t%f' % (r_int, l_int)
        l_com = l_complexity[i] / num_studies
        r_com = r_complexity[i] / num_studies
        print 'COMPLEXITY\t%f\t%f' % (r_com, l_com)
        l_str = l_structured[i] / num_studies
        r_str = r_structured[i] / num_studies
        print 'STRUCTURE\t%f\t%f' % (r_str, l_str)
        l_sur = l_surprising[i] / num_studies
        r_sur = r_surprising[i] / num_studies
        print 'SURPRISING\t%f\t%f' % (r_sur, l_sur)
        l_sat = l_satisfying[i] / num_studies
        r_sat = r_satisfying[i] / num_studies
        print 'SATISFYING \t%f\t%f' % (r_sat, l_sat)

        print

    all_sections = num_studies * 3
    print 'ACROSS SECTIONS'
    print 'FEATURE\t\tRAND_AVG\tLEARN_AVG'
    l_coh = sum(l_coherence) / all_sections
    r_coh = sum(r_coherence) / all_sections
    print 'COH\t\t%f\t%f' % (r_coh, l_coh)
    l_mus = sum(l_musical) / all_sections
    r_mus = sum(r_musical) / all_sections
    print 'MUSICAL\t\t%f\t%f' % (r_mus, l_mus)
    l_int = sum(l_interesting) / all_sections
    r_int = sum(r_interesting) / all_sections
    print 'INTERESTING\t%f\t%f' % (r_int, l_int)
    l_com = sum(l_complexity) / all_sections
    r_com = sum(r_complexity) / all_sections
    print 'COMPLEXITY\t%f\t%f' % (r_com, l_com)
    l_str = sum(l_structured) / all_sections
    r_str = sum(r_structured) / all_sections
    print 'STRUCTURE\t%f\t%f' % (r_str, l_str)
    l_sur = sum(l_surprising) / all_sections
    r_sur = sum(r_surprising) / all_sections
    print 'SURPRISING\t%f\t%f' % (r_sur, l_sur)
    l_sat = sum(l_satisfying) / all_sections
    r_sat = sum(r_satisfying) / all_sections
    print 'SATISFYING \t%f\t%f' % (r_sat, l_sat)










