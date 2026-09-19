import { Injectable } from '@angular/core';
import { DataSheetGenerateService } from "./data-sheet-generate.service";
import { NotificationService } from "./notification.service";
import { firstValueFrom } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class DSGHandler {

    constructor(
        private datasheetService: DataSheetGenerateService,
        private notificationService: NotificationService
    ) { }


    private roundingRules: { [key: string]: number } = {
        Rp02: 2,
        Rm: 2,
        Ag: 4,
        Agt: 4,
        A80: 4,
        E: 1,
        E_c: 2,
        nu: 3,
        nu_c: 5,
        r4_6: 4,
        r8_12: 4,
        r2_20: 4,
        r10_15: 4,
        n4_6: 4,
        n10_15: 4,
        n10_20: 4,
        n2_20: 4,
    };

    private dfYieldDesiredOrder: string[] = [
        "Aging days",
        "r8-12 0",
        "r8-12 45",
        "r8-12 90",
        "rbi",
        "σi/σ0 0",
        "σi/σ0 45",
        "σi/σ0 90",
        "σb/σ0",
    ];

    calculateAvgBulgeScaleFactor(dataSheetResults: any, bulgeSelectedOptions: string[]): number {
        if (!dataSheetResults?.bulge_scale_factor?.scale_factor_bulge || !bulgeSelectedOptions) {
            return 0;
        }

        const includedFiles = dataSheetResults.bulge_scale_factor.scale_factor_bulge.filter((item: any) =>
            bulgeSelectedOptions.includes(item.file)
        );

        const totalScaleFactor = includedFiles.reduce((sum: number, item: any) => sum + item.k, 0);
        const averageScaleFactor = includedFiles.length > 0 ? totalScaleFactor / includedFiles.length : 0;

        return averageScaleFactor;
    }

    getDfYieldKeys(dfYield: Record<string, string> | undefined): string[] {
        if (!dfYield) {
            return [];
        }

        const keys = Object.keys(dfYield);

        return this.dfYieldDesiredOrder.filter((key) =>
            key === "Aging days"
                ? keys.some((k) => k.toLowerCase() === "aging days")
                : keys.includes(key)
        );
    }

    getDfYieldValues(dfYield: Record<string, string> | undefined): { key: string; value: string }[] {
        if (!dfYield) {
            return [];
        }

        const keys = this.getDfYieldKeys(dfYield);

        return keys.map((key) => {
            const normalizedKey = key.toLowerCase() === "aging days" ? "aging days" : key;
            return { key, value: dfYield[normalizedKey] || "" };
        });
    }

    hasDfYieldData(dfYield: Record<string, string> | undefined): boolean {
        return !!dfYield && Object.keys(dfYield).length > 0;
    }

    extractFileName(fullPath: string): string {
        if (!fullPath) return '';
        const parts = fullPath.split('/');
        return parts[parts.length - 1];
    }

    getTensilePropertyColumnNames(jsonData: any): string[] {
        if (!jsonData || typeof jsonData !== 'object') {
            return [];
        }
        const allKeys = Object.keys(jsonData).filter(key => key !== 'file_name');
        const remainingKeys = allKeys.filter(key => key !== 'sampleId' && key !== 'included');
        const orderedColumns = [];
        if (allKeys.includes('sampleId')) orderedColumns.push('sampleId');
        if (allKeys.includes('included')) orderedColumns.push('included');
        orderedColumns.push(...remainingKeys);
        return orderedColumns;
    }

    updateTensileSampleInclusion(fileName: string, tensileSampleData: any[], tensileExcludedData: any[]): void {
        if (tensileSampleData) {
            const sampleIndex = tensileSampleData.findIndex((sample: any) => sample.sampleId === fileName || sample.file_name === fileName);
            if (sampleIndex !== -1) {
                const isExcluded = tensileExcludedData.some(
                    (excluded: any) => excluded.file_name === fileName
                );
                tensileSampleData[sampleIndex].included = isExcluded ? 'no' : 'yes';
            }
        }
    }

    sortTensileSampleData(data: any[]): any[] {
        if (!data || data.length === 0) return [];
        const sortedData = [...data];
        const sampleIds = sortedData.map((row: any) => row.sampleId);
        const sortedSampleIds = this.sortOptions(sampleIds);
        return sortedData.sort((a: any, b: any) => {
            const indexA = sortedSampleIds.indexOf(a.sampleId);
            const indexB = sortedSampleIds.indexOf(b.sampleId);
            return indexA - indexB;
        });
    }

    private sortOptions(options: string[]): string[] {
        return options.sort((a, b) => a.localeCompare(b));
    }

    getFilteredAndSortedTensileData(direction: string, tensileSampleData: any[]): any[] {
        const filteredData = tensileSampleData.filter((row: any) => this.getDirectionFromSampleId(row.sampleId) === direction);
        return this.sortTensileSampleData(filteredData);
    }

    getDirectionFromSampleId(sampleId: string): string {
        const parts = sampleId.split('_');
        return parts[3];
    }

    async readTensileCSV(
        siteID: string,
        projectId: string,
        datasheetId: any,
        nominalAge: any,
        dataSheetResults: any
    ): Promise<any> {
        if (!siteID || !projectId || !datasheetId || !nominalAge) {
            this.notificationService.showError('Missing required parameters for fetching tensile statistics');
            throw new Error('Missing parameters');
        }

        if (!dataSheetResults || !dataSheetResults.tensile_sample_data) {
            this.notificationService.showError('Incomplete tensile properties results');
            throw new Error('Incomplete data');
        }

        const obj = {
            project_id: projectId,
            datasheet: datasheetId,
            nominal_age: nominalAge,
            file_path: dataSheetResults?.tensile_sample_data,
        };

        const response = await firstValueFrom(this.datasheetService.readCSV(obj));
        if (!response) {
            this.notificationService.showError('No response received from the server');
            throw new Error('No response');
        }
        if (!response.csv_data || response.csv_data.length === 0) {
            this.notificationService.showError('No CSV data found in response');
            throw new Error('Empty CSV data');
        }
        return response.csv_data;
    }

    async fetchTensileSampleData(
        csvData: any,
        siteID: string,
        projectId: string,
        datasheetId: any,
        nominalAge: any
    ): Promise<any> {
        const response = await firstValueFrom(this.datasheetService.getTensileSampleData(siteID, projectId, datasheetId, nominalAge, csvData));
        if (!response) {
            this.notificationService.showError('No tensile sample data received');
            throw new Error('No response');
        }
        return response;
    }
}