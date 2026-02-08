import {
  Controller,
  Get,
  Post,
  Body,
  UseGuards,
  InternalServerErrorException,
} from '@nestjs/common';
import { PortfolioService } from './portfolio.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';

@Controller('portfolio')
export class PortfolioController {
  constructor(private readonly portfolioService: PortfolioService) {}

  @UseGuards(JwtAuthGuard)
  @Post('recommend')
  async recommend(@Body() body: { profile?: string }) {
    try {
      return await this.portfolioService.recommend(body.profile ?? 'modere');
    } catch (err) {
      throw new InternalServerErrorException(
        `Recommendation failed: ${(err as Error).message}`,
      );
    }
  }

  @UseGuards(JwtAuthGuard)
  @Post('simulate')
  async simulate(
    @Body() body: { profile?: string; capital?: number; days?: number },
  ) {
    try {
      return await this.portfolioService.simulate(
        body.profile ?? 'modere',
        body.capital,
        body.days,
      );
    } catch (err) {
      throw new InternalServerErrorException(
        `Simulation failed: ${(err as Error).message}`,
      );
    }
  }

  @UseGuards(JwtAuthGuard)
  @Post('stress-test')
  async stressTest(
    @Body() body: { stress_type?: string; intensity?: number },
  ) {
    try {
      return await this.portfolioService.stressTest(
        body.stress_type ?? 'sector_crash',
        body.intensity ?? 0.2,
      );
    } catch (err) {
      throw new InternalServerErrorException(
        `Stress test failed: ${(err as Error).message}`,
      );
    }
  }

  @UseGuards(JwtAuthGuard)
  @Get('snapshot')
  async getPortfolio() {
    try {
      return await this.portfolioService.getPortfolio();
    } catch (err) {
      throw new InternalServerErrorException(
        `Portfolio snapshot failed: ${(err as Error).message}`,
      );
    }
  }

  @UseGuards(JwtAuthGuard)
  @Get('macro')
  async getMacro() {
    try {
      return await this.portfolioService.getMacro();
    } catch (err) {
      throw new InternalServerErrorException(
        `Macro data failed: ${(err as Error).message}`,
      );
    }
  }

  @UseGuards(JwtAuthGuard)
  @Post('train')
  async train(
    @Body()
    body: { timesteps?: number; adversarial?: boolean; rounds?: number },
  ) {
    try {
      return await this.portfolioService.train(
        body.timesteps,
        body.adversarial,
        body.rounds,
      );
    } catch (err) {
      throw new InternalServerErrorException(
        `Training failed: ${(err as Error).message}`,
      );
    }
  }
}
