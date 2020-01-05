<template>
    <div class="row">
      <div class="col-md-12">
        <card>
          <template slot="header">
            <h4 class="card-title">Meta-Model Status</h4>
            <table class="table table-hover">
              <thead>
              <th>Meta-Model</th>
              <th>Status</th>
              <th>Operation</th>
              </thead>
              <tbody>
              <tr v-for="metamodel in metamodels">
                <td>{{ metamodel.metamodel }}</td>
                <td>
                  <div v-if="metamodel.status === 'online'" class="dbadge dbadge-ok">online</div>
                  <div v-else class="dbadge dbadge-danger">offline</div>
                </td>
                <td>
                  <p-button
                    v-if="metamodel.status === 'online'"
                    class="icon-button"
                    v-on:click="buildMetamodel(metamodel.metamodel)">
                    <i class="ti-reload icon-padded"></i>Rebuild</p-button>
                  <p-button
                    v-else class="icon-button"
                    v-on:click.native="buildMetamodel(metamodel.metamodel)">
                    <i class="ti-hummer icon-padded"></i>Build</p-button>
                </td>
              </tr>
              </tbody>
            </table>
          </template>
        </card>
      </div>

    </div>
</template>
<script>
  import {eventBus} from "../assets/js/EventBus";
  import {context} from "../assets/js/context";

  export default {
    data: function() {
      return {
        metamodels: []
      }
    },
    mounted: function () {
      eventBus.$on("metamodelsUpdated", () => {
        this.metamodels = context.listMetamodels();
      })
    },
    methods: {
      buildMetamodel: function (metamodelName) {
        context.buildMetamodel(metamodelName);
      }
    }
  };
</script>
<style>
</style>
