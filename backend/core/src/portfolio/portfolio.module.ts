import { Module } from '@nestjs/common';
import { PortfolioService } from './portfolio.service.js';
import { PortfolioController } from './portfolio.controller.js';
import { AuthModule } from '../auth/auth.module.js';

@Module({
  imports: [AuthModule],
  controllers: [PortfolioController],
  providers: [PortfolioService],
})
export class PortfolioModule {}
