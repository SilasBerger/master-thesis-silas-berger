<template>
  <div>
    <div id="statistics-root" v-if="statisticsFetched">
      <!--Stats cards-->
      <div class="row">
        <div class="col-md-6 col-xl-3" v-for="stats in statsCards" :key="stats.title">
          <stats-card>
            <div class="icon-big text-center" :class="`icon-${stats.type}`" slot="header">
              <i :class="stats.icon"></i>
            </div>
            <div class="numbers" slot="content">
              <p>{{stats.title}}</p>
              {{stats.value}}
            </div>
          </stats-card>
        </div>
      </div>

      <!--Charts-->
      <div class="row">

        <div class="col-md-6 col-12">
          <chart-card title="Influencers by Category"
                      sub-title="Subcategories Aggregated"
                      :chart-data="influencersChart.data"
                      chart-type="Pie">
            <div slot="legend">
              <i class="fa fa-circle text-info"></i> Politics
              <i class="fa fa-circle text-warning"></i> Media
              <i class="fa fa-circle text-danger"></i> Sports
              <i class="fa fa-circle text-success"></i> Other
            </div>
          </chart-card>
        </div>

        <div class="col-md-6 col-12">
          <chart-card title="Users Train / Validate / Test Dataset"
                      sub-title="Swiss / Foreign Split"
                      :chart-data="tvtUsersChart.data"
                      chart-type="Pie">

            <div slot="legend">
              <i class="fa fa-circle text-info"></i> Swiss
              <i class="fa fa-circle text-warning"></i> Foreign
            </div>
          </chart-card>
        </div>

      </div>
    </div>
  </div>
</template>
<script>
    import { StatsCard, ChartCard } from "@/components/index";
    import Chartist from 'chartist';
    import {context} from "../assets/js/context";
    import {eventBus} from "../assets/js/EventBus";
    import {formatLargeNumber} from "../assets/js/util"
    export default {
        components: {
            StatsCard,
            ChartCard
        },
        /**
         * Chart data used to render stats, charts. Should be replaced with server data
         */
        data() {
            return {
                statisticsFetched: false,
                statistics: null,
                statsCards: [
                    {
                        type: "success",
                        icon: "ti-user",
                        title: "Users",
                        value: "0"
                    },
                    {
                        type: "success",
                        icon: "ti-ruler-alt-2",
                        title: "Train / Test",
                        value: "0"
                    },
                    {
                        type: "success",
                        icon: "ti-thumb-up",
                        title: "Influencers",
                        value: "0"
                    },
                    {
                        type: "info",
                        icon: "ti-twitter-alt",
                        title: "Tweets",
                        value: "0",
                    }
                ],
                influencersChart: {
                    data: {
                        labels: ["64%", "25%", "10%", "1%"],
                        series: [64, 25, 10, 1]
                    },
                    options: {}
                },
                tvtUsersChart: {
                    data: {
                        labels: ["0%", "100%"],
                        series: [0, 100]
                    },
                    options: {}
                }
            };
        },
      mounted: function () {
        const stats = context.getStatistics();
        if (stats == null) {
          // Need to load stats first, call me back when done, and I'll fetch them
          eventBus.$on("statisticsLoaded", () => {
            this.statisticsFetched = true;
            this.statistics = context.getStatistics();
            this.onStatsFetched();
          })
        } else {
          // Stats already loaded, can use return value
          this.statisticsFetched = true;
          this.statistics = stats;
          this.onStatsFetched();
        }
      },
      methods: {
        onStatsFetched: function () {

          // Stats Cards
          this.statsCards = [
            {
              type: "success",
              icon: "ti-user",
              title: "Users",
              value: formatLargeNumber(this.statistics.usersCount)
            },
            {
              type: "success",
              icon: "ti-ruler-alt-2",
              title: "Train / Test",
              value: formatLargeNumber(this.statistics.tvtUsersCount)
            },
            {
              type: "success",
              icon: "ti-thumb-up",
              title: "Influencers",
              value: formatLargeNumber(this.statistics.influencersCount)
            },
            {
              type: "info",
              icon: "ti-twitter-alt",
              title: "Tweets",
              value: formatLargeNumber(this.statistics.tweetsCount),
            }
          ];

          // Influencers Chart
          const mediaPercentage = ((this.statistics.mediaInfluencersCount / this.statistics.influencersCount) * 100).toFixed(1);
          const sportsPercentage = ((this.statistics.sportsInfluencersCount / this.statistics.influencersCount) * 100).toFixed(1);
          const politicsPercentage = ((this.statistics.politicsInfluencersCount / this.statistics.influencersCount) * 100).toFixed(1);
          const otherPercentage = ((this.statistics.otherInfluencersCount / this.statistics.influencersCount) * 100).toFixed(1);

          this.influencersChart = {
            data: {
              labels: [mediaPercentage + "%", sportsPercentage + "%", politicsPercentage + "%", otherPercentage + "%"],
                series: [mediaPercentage, sportsPercentage, politicsPercentage, otherPercentage]
            },
            options: {}
          };

          // TVT Chart
          const swissPercentage = ((this.statistics.tvtSwissUsersCount / this.statistics.tvtUsersCount) * 100).toFixed(0);
          const foreignPercentage = 100 - swissPercentage;
          this.tvtUsersChart = {
            data: {
              labels: [swissPercentage + "%", foreignPercentage + "%"],
                series: [swissPercentage, foreignPercentage]
            },
            options: {}
          }
        }
      }
    };
</script>
<style>
</style>
