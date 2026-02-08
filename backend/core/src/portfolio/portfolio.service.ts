import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class PortfolioService {
  private readonly logger = new Logger(PortfolioService.name);
  private readonly baseUrl: string;

  constructor(private readonly configService: ConfigService) {
    this.baseUrl =
      this.configService.get<string>('PORTFOLIO_SERVICE_URL') ??
      'http://localhost:8003';
  }

  private async forward(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<any> {
    const url = `${this.baseUrl}/api/v1${path}`;
    this.logger.log(`${method} ${url}`);

    const opts: RequestInit = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(url, opts);

    if (!res.ok) {
      const text = await res.text();
      this.logger.error(`Portfolio service error ${res.status}: ${text}`);
      throw new Error(`Portfolio service returned ${res.status}: ${text}`);
    }

    return res.json();
  }

  async recommend(profile: string) {
    return this.forward('POST', '/recommend', { profile });
  }

  async simulate(profile: string, capital?: number, days?: number) {
    return this.forward('POST', '/simulate', { profile, capital, days });
  }

  async stressTest(stressType: string, intensity: number) {
    return this.forward('POST', '/stress-test', {
      stress_type: stressType,
      intensity,
    });
  }

  async getPortfolio() {
    return this.forward('GET', '/portfolio');
  }

  async getMacro() {
    return this.forward('GET', '/macro');
  }

  async train(timesteps?: number, adversarial?: boolean, rounds?: number) {
    return this.forward('POST', '/train', { timesteps, adversarial, rounds });
  }
}
