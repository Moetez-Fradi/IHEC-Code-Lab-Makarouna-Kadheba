import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { BvmtData } from './bvmt-data.entity.js';
import { MarketService } from './market.service.js';
import { MarketController } from './market.controller.js';
import { AuthModule } from '../auth/auth.module.js';

@Module({
  imports: [TypeOrmModule.forFeature([BvmtData]), AuthModule],
  controllers: [MarketController],
  providers: [MarketService],
})
export class MarketModule {}
