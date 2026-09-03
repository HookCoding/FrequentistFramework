import os
import re
import shutil
import sys

from run_execution import execute


def replaceinfile(f, old_new_list):
    with open(f, "r") as file:
        filedata = file.read()

    try:
        for tup in old_new_list:
            filedata = re.sub(tup[0], tup[1], filedata)
    except Exception:
        print("ERROR: replaceinfile expects a list of tuples of strings [(old1,new1),...] as input")
        print(old_new_list)
        sys.exit(-1)

    with open(f, "w") as file:
        file.write(filedata)


def _seed_prefit_parameters(
    datafile,
    datahist,
    rangelow,
    rangehigh,
    backgroundfile,
    tmpbackgroundfile,
    nbkg,
):
    from PreFit import PreFitter

    nPars = 5

    if "three" in backgroundfile:
        nPars = 3
    if "four" in backgroundfile:
        nPars = 4
    elif "five" in backgroundfile:
        nPars = 5
    elif "six" in backgroundfile:
        nPars = 6
    elif "seven" in backgroundfile:
        nPars = 7
    elif "eight" in backgroundfile:
        nPars = 8
    elif "nine" in backgroundfile:
        nPars = 9
    elif "ten" in backgroundfile:
        nPars = 10
    # [1, -30, -30, -30, ...]
    parRangeLow = [1] + [-30] * (nPars - 1)
    parRangeHigh = [1] + [30] * (nPars - 1)

    # get prefit ranges from background file
    with open(tmpbackgroundfile) as f:
        lines = f.readlines()
        for line in lines:
            if "<!--" not in line and "<ModelItem" in line:
                matches = re.findall(
                    r"\[PAR(\d+),[ ]*([+-]?[0-9]+(?:[.][0-9]*)?),"
                    r"[ ]*([+-]?[0-9]+(?:[.][0-9]*)?)[ ]*\]",
                    line,
                )
                for m in matches:
                    # m[0] is parN
                    # m[1] is rangeLow
                    # m[2] is rangeHigh
                    parRangeLow[int(m[0]) - 1] = float(m[1])
                    parRangeHigh[int(m[0]) - 1] = float(m[2])

    print("Starting PreFit in parameter ranges:")
    print(parRangeLow)
    print(parRangeHigh)

    pf = PreFitter(
        datafile=datafile,
        datahist=datahist,
        xMin=rangelow,
        xMax=rangehigh,
        nPars=nPars,
        nRetries1=2000 * nPars,
        nRetries2=2 * nPars,
        fitLog=True,
        parRangeLow=parRangeLow,
        parRangeHigh=parRangeHigh,
    )

    initPars, _nbkg = pf.Fit()
    print(_nbkg)
    nbkg = "%.1E, 0, %.1E" % (_nbkg, 2 * _nbkg)
    print(_nbkg)

    print("Starting fit with initial pars", initPars)

    for i in range(nPars):
        replaceinfile(tmpbackgroundfile, [("PAR%d" % (i + 1), str(initPars[i]))])

    return nbkg


def _stage_xml_templates(
    folder,
    topfile,
    categoryfile,
    backgroundfile,
    signalfile,
    signame,
    wsfile,
    sigmean,
    sigwidth,
    datafile,
    datahist,
    rangelow,
    rangehigh,
    nbkg,
    nsig,
    doprefit,
    systdict,
):
    nbins = rangehigh - rangelow

    # generate the config files on the fly in run dir
    if not os.path.isfile("{}/AnaWSBuilder.dtd".format(folder)):
        # execute("ln -sf $PWD/config/dijetTLA/AnaWSBuilder.dtd "
        #         "$PWD/{}/AnaWSBuilder.dtd".format(folder))
        # execute("ln -sf ~/WORK/tla/FrequentistFramework/config/dijetisrTLA/"
        #         "AnaWSBuilder.dtd {}/AnaWSBuilder.dtd".format(folder))
        execute(
            "ln -sf `realpath config/dijetisrTLA/AnaWSBuilder.dtd` {}/AnaWSBuilder.dtd".format(
                folder
            )
        )
        print("this is happening")
    if sigwidth == -999:  # running on zprime samples:
        print("Running in Zprime samples")
        tmpcategoryfile = "{0}/category_dijetTLA_fromTemplate_mR{1}.xml".format(folder, sigmean)
        tmptopfile = "{0}/dijetTLA_fromTemplate_mR{1}.xml".format(folder, sigmean)
    else:
        tmpcategoryfile = "{}/category_dijetTLA_fromTemplate.xml".format(folder)
        tmptopfile = "{}/dijetTLA_fromTemplate.xml".format(folder)
    tmpsignalfile = "{}/signal_dijetTLA_fromTemplate.xml".format(folder)
    tmpbackgroundfile = "{}/background_dijetTLA_fromTemplate.xml".format(folder)

    # XMLReader resolves relative paths from the current working directory.
    # Keep full paths for Python file operations, but write portable paths
    # relative to the repository working directory into generated XML files.
    xml_categoryfile = os.path.relpath(tmpcategoryfile, os.getcwd())
    xml_signalfile = os.path.relpath(tmpsignalfile, os.getcwd())
    xml_backgroundfile = os.path.relpath(tmpbackgroundfile, os.getcwd())
    xml_wsfile = os.path.relpath(wsfile, os.getcwd())

    print("--------------------------------------> tmpcategoryfile: " + tmpcategoryfile)
    print("--------------------------------------> tmptopfile: " + tmptopfile)

    shutil.copy2(topfile, tmptopfile)
    shutil.copy2(categoryfile, tmpcategoryfile)
    if signalfile:
        shutil.copy2(signalfile, tmpsignalfile)

    replaceinfile(
        tmptopfile,
        [
            ("CATEGORYFILE", xml_categoryfile),
            ("OUTPUTFILE", xml_wsfile),
            ("SIGNAME", signame),
        ],
    )

    if backgroundfile:
        shutil.copy2(backgroundfile, tmpbackgroundfile)
        replaceinfile(tmpcategoryfile, [("BACKGROUNDFILE", xml_backgroundfile)])

        if doprefit:
            nbkg = _seed_prefit_parameters(
                datafile=datafile,
                datahist=datahist,
                rangelow=rangelow,
                rangehigh=rangehigh,
                backgroundfile=backgroundfile,
                tmpbackgroundfile=tmpbackgroundfile,
                nbkg=nbkg,
            )

    replaceinfile(
        tmpcategoryfile,
        [
            ("DATAFILE", datafile),
            ("DATAHIST", datahist),
            ("RANGELOW", str(rangelow)),
            ("RANGEHIGH", str(rangehigh)),
            ("BINS", str(nbins)),
            ("NBKG", nbkg),
            ("NSIG", nsig),
            ("SIGNAME", signame),
            ("SIGNALFILE", xml_signalfile),
        ],
    )

    if signalfile:
        # replaceinfile(tmpsignalfile,
        #               [("SIGMEAN", str(sigmean)),
        #                ("SIGWIDTH", str(sigwidth)),
        # ])
        replacements = [
            ("SIGNAME", str(signame)),
            ("SIGMEAN", str(sigmean)),
            ("SIGWIDTH", str(sigwidth)),
        ]

        if systdict is not None:
            print("replacing in signalfile now")
            replacements.append(("NOMINAL_MEAN", str(systdict["nominal_mean"])))
            replacements.append(("NOMINAL_WIDTH", str(systdict["nominal_sigma"])))
            replacements.append(("NOMINAL_ALPHAL", str(systdict["nominal_alpha_l"])))
            replacements.append(("NOMINAL_ALPHAH", str(systdict["nominal_alpha_h"])))
            replacements.append(("NOMINAL_NL", str(systdict["nominal_n_l"])))
            replacements.append(("NOMINAL_NH", str(systdict["nominal_n_h"])))
            for source in systdict["unc_mean_sources"]:
                val = systdict["unc_mean_sources"][source]
                replacements.append((r"\[MAG_SCALE_" + str(source) + r"\]", "[" + str(val) + "]"))
            for source in systdict["unc_sigma_sources"]:
                val = systdict["unc_sigma_sources"][source]
                replacements.append(
                    (r"\[MAG_RESOLUTION_" + str(source) + r"\]", "[" + str(val) + "]")
                )

        #  if covariancedict != None:
        #      print("replacing in signalfile now")
        #      replacements.append(("NOMINAL_MEAN", str(covariancedict["nominal_mean"])))
        #      replacements.append(("NOMINAL_WIDTH", str(covariancedict["nominal_sigma"])))
        #      replacements.append(("NOMINAL_ALPHAL", str(covariancedict["nominal_alpha_l"])))
        #      replacements.append(("NOMINAL_ALPHAH", str(covariancedict["nominal_alpha_h"])))
        #      replacements.append(("NOMINAL_NL", str(covariancedict["nominal_n_l"])))
        #      replacements.append(("NOMINAL_NH", str(covariancedict["nominal_n_h"])))
        #      replacements.append(("MAG_SCALE",
        #          str(covariancedict["covariance_cholesky"][4][4])))
        #      replacements.append(("MAG_RESOLUTION",
        #          str(covariancedict["covariance_cholesky"][5][5])))
        #      replacements.append(("MAG_CROSSTERM",
        #          str(covariancedict["covariance_cholesky"][5][4])))

        # set any unreplaced uncertainties to 0 (starting with MAG_ and then
        # any letters, numbers or _ -):
        replacements.append((r"\[MAG_[a-zA-Z0-9_\-]*\]", "[0]"))
        replaceinfile(tmpsignalfile, replacements)

    return tmptopfile, tmpcategoryfile, xml_categoryfile, xml_wsfile


def prepare_run_templates(
    folder,
    topfile,
    categoryfile,
    backgroundfile,
    signalfile,
    signame,
    wsfile,
    sigmean,
    sigwidth,
    datafile,
    datahist,
    rangelow,
    rangehigh,
    nbkg,
    nsig,
    doprefit,
    systdict,
):
    return _stage_xml_templates(
        folder=folder,
        topfile=topfile,
        categoryfile=categoryfile,
        backgroundfile=backgroundfile,
        signalfile=signalfile,
        signame=signame,
        wsfile=wsfile,
        sigmean=sigmean,
        sigwidth=sigwidth,
        datafile=datafile,
        datahist=datahist,
        rangelow=rangelow,
        rangehigh=rangehigh,
        nbkg=nbkg,
        nsig=nsig,
        doprefit=doprefit,
        systdict=systdict,
    )
