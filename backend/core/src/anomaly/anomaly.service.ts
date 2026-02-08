import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class AnomalyService {
  private readonly logger = new Logger(AnomalyService.name);
  private readonly baseUrl: string;

  constructor(private readonly configService: ConfigService) {
    this.baseUrl =
      this.configService.get<string>('ANOMALY_SERVICE_URL') ??
      'http://localhost:8001';
  }

  /**
   * Forward the anomaly-detection request to the Python micro-service
   * and return the JSON report as-is.
   */
  async getAnomalies(
    code: string,
    start: string,
    end: string,
  ): Promise<any> {
    const url = `${this.baseUrl}/anomalies?code=${encodeURIComponent(code)}&start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`;

    this.logger.log(`Calling anomaly service: ${url}`);

    const res = await fetch(url);

    if (!res.ok) {
      const body = await res.text();
      this.logger.error(`Anomaly service error ${res.status}: ${body}`);
      throw new Error(`Anomaly service returned ${res.status}: ${body}`);
    }

    return res.json();
  }
}
