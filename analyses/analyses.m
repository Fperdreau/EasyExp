function analyses(doImport, pilot)
% This function runs data analysis
% @param bool doImport: shall we import data (true or 1) or load data from previous run (false or 0)
% @param string pilot: perform analysis on set from a specific version of the experiment (! data must be stored in analyses/data/version_name/)
%
% Usage:
% Participants' data folder should be stored in analyses/data or in analyses/data/version_name/, with one folder per participant:
%   analyses/data/participant_1/ or analyses/data/v1.0.0/participant_1
% Examples:
% If we want to import and analyse data
% analyses(1)
%
% If we want to import and analyse data from a specific version of the experiment
% analyses(1, 'v1.0.0')
%
% @author: Florian Perdreau (f.perdreau@donders.ru.nl)


    % Reset workspace
    close all; home;

    % Parse input arguments
    if nargin == 0
        doImport = true;
        pilot = '';
    elseif nargin < 2
        pilot = '';
    end

    % Setup environment
    % Get folders
    x = what;
    root = x.path;
    
    % Add libraries and dependencies to watched path
    PATH_TO_LIBS = '../../../../Experiment framework/Functions/';
    PATH_TO_VENDORS = fullfile(root, 'vendors');
    addpath(genpath(PATH_TO_LIBS));
    addpath(genpath(PATH_TO_VENDORS));

    % List of selected participants (if specified, only those participants 
    % will be analysed)
    selected = {}; 
    
    % List of excluded participants
    excluded = {'demo','backup'};
    
    if ~strcmp(pilot,'')
        pilotdata = fullfile('backup',pilot);
    else
        pilotdata = '';
    end
    
    datafolder = fullfile(root,'data',pilotdata); % Data folder
    figFolder = fullfile('figures',pilot); % Figures folder
    if ~isdir(figFolder)
        mkdir(figFolder);
    end
    
    subList = getcontent(datafolder,'dir');
    subList = subList(~ismember(subList,excluded));
    if ~isempty(selected)
        subList = subList(ismember(subList,selected));
    end
        
    datafilename = fullfile(datafolder,'Data.mat');
    conditions = {'Dynamic'};

    if doImport
        results = struct;
        for c = 1:numel(conditions)

            conditionName = conditions{c};
            results.(conditionName) = struct;
            % Import behavioral design
            fprintf('\nImporting designs...');
            results.(conditionName) = ImportFile(results.(conditionName), datafolder, subList, conditionName, 'design');
            
            % Import behavioral data
            fprintf('\nImporting behavioral data...');
            results.(conditionName) = ImportFile(results.(conditionName), datafolder, subList, conditionName, 'data');

            % Pre-processing/Filtering data
            results.(conditionName) = some_preprocessing_function(results.(conditionName));

        end
        % Save all data
        save(datafilename,'results','subList','conditions');
    else
        if exist(datafilename,'file')
            load(datafilename,'results','subList','conditions');
        end
    end

    % Perform data analysis
    for c = 1:numel(conditions)

        %% Only call analysis scripts if we got some data for this condition
        if size(results.(conditionName).subjects,1)>0
            fprintf('\n..:: Analyzing %s :...',conditionName);

            % Run some analysis
            % e.g.: results.(conditionName) = some_analysis_function(results.(conditionName));
            fprintf('Completed\n');
        end
    end

    % Save results
    save(datafilename,'results','subList','conditions');

    fprintf('\nAnalyses Completed\n');

end


