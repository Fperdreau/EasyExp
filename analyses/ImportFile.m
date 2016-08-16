% This file is part of EasyPsy

function [ results ] = ImportFile( results, datafolder, subList, conditionName, content)
% ImportFile
% This function scans a data folder and import data file
% Usage: results = ImportFile(results, datafolder, subList, conditionName, content)
% @param results struct: structure array to update
%   example: results
%       results.subjects.XX.name
%                          .data
% @param datafolder string: data folder to scan
% @param subList cell-array: list of subjects
% @param conditionName string: name of the condition (used to select the
% files to parse
% @param content string: type of file to parse (e.g 'data' or 'design')
% @return results struct: updated structure
% @author: Florian Perdreau (f.perdreau@donders.ru.nl)

nsub = numel(subList);

for s = 1:nsub
    subName = subList{s};
    fprintf('\nSubject: %s | ',subName);
    
    subFolder = fullfile(datafolder,subName);
    subfiles = getcontent(subFolder,'file','txt');
    selectedFiles = strfind(subfiles,content);
    data = [];
    nprocessed = 0;
    for f = 1:numel(selectedFiles)
        if ~isempty(selectedFiles{f}) && isempty(strfind(subfiles{f},'practice'))
            filename = subfiles{f};

            split = strsplit(filename, '_');
            condition = split{2};
            if ~strcmp(condition,conditionName)
                continue
            end
            nprocessed = nprocessed + 1;
            session = str2double(split{3});
            ds = dataset('File',fullfile(subFolder,filename),'Delimiter',',');
            
            ds.id = repmat(subName,size(ds,1),1);
            ds.condition = repmat(condition,size(ds,1),1);
            ds.session = repmat(session,size(ds,1),1);

            if exist('data','var')
                data = [data;ds];
            else
                data = ds;
            end
        end
    end
    
    if nprocessed > 0
        results.subjects.(subName).name = subName;
        results.subjects.(subName).(content) = data;
    end
    clear data;
    fprintf('%d files processed\n',nprocessed);
end

end

